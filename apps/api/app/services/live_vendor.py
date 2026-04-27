from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json

import httpx

from ..config import get_settings
from ..models import FeatureSnapshotModel, FeedSnapshotModel, ReplayPointModel
from ..repositories.feature_repository import FeatureRepository
from ..repositories.feed_repository import FeedRepository
from ..repositories.incident_repository import IncidentRepository
from ..repositories.ingestion_repository import IngestionRepository
from ..repositories.replay_repository import ReplayRepository
from ..scoring import ReliabilityInputs, classify_status, compute_weighted_trust_score


LIVE_FEATURE_ID = "feat-order-imbalance"
LIVE_INCIDENT_ID = "inc-live-feed-binance-agg"


@dataclass(frozen=True)
class BinanceSnapshot:
    symbol: str
    avg_price: float
    last_price: float
    price_change_pct: float
    latency_seconds: int
    schema_version: str
    bid_qty: float
    ask_qty: float
    trade_count: int
    quote_volume: float
    computed_at: datetime
    replay_points: list[ReplayPointModel]


class BinanceSpotConnector:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _get_json(self, path: str, params: dict[str, str | int]) -> dict | list:
        with httpx.Client(
            base_url=self.settings.live_vendor_base_url,
            timeout=self.settings.live_vendor_timeout_seconds,
        ) as client:
            response = client.get(path, params=params)
            response.raise_for_status()
            return response.json()

    def fetch_snapshot(self, symbol: str, freshness_sla_seconds: int) -> BinanceSnapshot:
        avg_price = self._get_json("/api/v3/avgPrice", {"symbol": symbol})
        ticker = self._get_json("/api/v3/ticker/24hr", {"symbol": symbol, "type": "FULL"})
        depth = self._get_json("/api/v3/depth", {"symbol": symbol, "limit": 5})
        trades = self._get_json("/api/v3/aggTrades", {"symbol": symbol, "limit": 10})

        computed_at = datetime.utcnow().replace(microsecond=0)
        close_time = datetime.utcfromtimestamp(int(ticker["closeTime"]) / 1000).replace(microsecond=0)
        latency_seconds = max(0, int((computed_at - close_time).total_seconds()))

        bid_qty = sum(float(level[1]) for level in depth["bids"])
        ask_qty = sum(float(level[1]) for level in depth["asks"])
        avg_price_value = float(avg_price["price"])
        weighted_trust = 100.0

        replay_points = [
            ReplayPointModel(
                feature_id=LIVE_FEATURE_ID,
                timestamp=datetime.utcfromtimestamp(int(trade["T"]) / 1000).replace(microsecond=0),
                expected_value=avg_price_value,
                actual_value=float(trade["p"]),
                trust_score=weighted_trust,
                blocked=False,
            )
            for trade in sorted(trades, key=lambda trade: trade["T"])
        ]

        return BinanceSnapshot(
            symbol=symbol,
            avg_price=avg_price_value,
            last_price=float(ticker["lastPrice"]),
            price_change_pct=float(ticker["priceChangePercent"]),
            latency_seconds=latency_seconds,
            schema_version="binance-spot-v3",
            bid_qty=bid_qty,
            ask_qty=ask_qty,
            trade_count=int(ticker["count"]),
            quote_volume=float(ticker["quoteVolume"]),
            computed_at=computed_at,
            replay_points=replay_points,
        )


class LiveFeedRefreshService:
    def __init__(self, session):
        self.session = session
        self.settings = get_settings()
        self.feed_repository = FeedRepository(session)
        self.feature_repository = FeatureRepository(session)
        self.replay_repository = ReplayRepository(session)
        self.ingestion_repository = IngestionRepository(session)
        self.incident_repository = IncidentRepository(session)
        self.connector = BinanceSpotConnector()

    def is_live_mode_enabled(self) -> bool:
        return self.settings.data_mode == "live"

    def is_live_feed(self, feed_id: str) -> bool:
        return self.is_live_mode_enabled() and feed_id == self.settings.live_vendor_feed_id

    def ensure_feed_is_current(self, feed_id: str) -> None:
        if not self.is_live_feed(feed_id):
            print(
                "live_refresh_skipped",
                {
                    "feed_id": feed_id,
                    "data_mode": self.settings.data_mode,
                    "configured_feed_id": self.settings.live_vendor_feed_id,
                },
            )
            return

        latest_snapshot = self.feed_repository.get_latest_snapshot_or_none(feed_id)
        if latest_snapshot is not None:
            age_seconds = int((datetime.utcnow().replace(microsecond=0) - latest_snapshot.computed_at).total_seconds())
            if (
                latest_snapshot.schema_version == "binance-spot-v3"
                and age_seconds <= self.settings.live_refresh_window_seconds
            ):
                print(
                    "live_refresh_cache_hit",
                    {
                        "feed_id": feed_id,
                        "age_seconds": age_seconds,
                        "schema_version": latest_snapshot.schema_version,
                    },
                )
                return

        print(
            "live_refresh_triggered",
            {
                "feed_id": feed_id,
                "symbol": self.settings.live_vendor_symbol,
                "data_mode": self.settings.data_mode,
            },
        )
        self.refresh_live_feed()

    def refresh_live_feed(self):
        feed_id = self.settings.live_vendor_feed_id
        feed = self.feed_repository.get_feed(feed_id)
        run = self.ingestion_repository.create_run(feed_id=feed_id, run_type="poll", status="running")

        try:
            snapshot = self.connector.fetch_snapshot(self.settings.live_vendor_symbol, feed.freshness_sla_seconds)

            freshness = max(
                0.0,
                min(
                    100.0,
                    round(100 - ((snapshot.latency_seconds / max(1, feed.freshness_sla_seconds)) * 100), 2),
                ),
            )
            completeness = 100.0
            schema_stability = 100.0
            entity_coverage = min(100.0, round((snapshot.trade_count / 1000) * 100, 2))
            revision_rate = 100.0
            drift_anomaly_score = max(0.0, round(100 - min(abs(snapshot.price_change_pct) * 4, 70), 2))
            weighted_trust = compute_weighted_trust_score(
                ReliabilityInputs(
                    freshness=freshness,
                    completeness=completeness,
                    schema_stability=schema_stability,
                    entity_coverage=entity_coverage,
                    revision_rate=revision_rate,
                    drift_anomaly_score=drift_anomaly_score,
                )
            )
            status = classify_status(weighted_trust)
            feature_value = round(
                (snapshot.bid_qty - snapshot.ask_qty) / max(snapshot.bid_qty + snapshot.ask_qty, 1.0),
                4,
            )

            feed_snapshot = self.feed_repository.create_snapshot(
                FeedSnapshotModel(
                    feed_id=feed_id,
                    computed_at=snapshot.computed_at,
                    freshness=freshness,
                    completeness=completeness,
                    schema_stability=schema_stability,
                    entity_coverage=entity_coverage,
                    revision_rate=revision_rate,
                    drift_anomaly_score=drift_anomaly_score,
                    weighted_trust_score=weighted_trust,
                    status=status,
                    latency_seconds=snapshot.latency_seconds,
                    schema_version=snapshot.schema_version,
                )
            )
            self.feed_repository.update_status(feed_id, status)

            self.feature_repository.create_snapshot(
                FeatureSnapshotModel(
                    feature_id=LIVE_FEATURE_ID,
                    feed_snapshot_id=feed_snapshot.id,
                    source_timestamp=snapshot.computed_at,
                    latest_value=feature_value,
                    trust_score=weighted_trust,
                    blocked=status == "critical",
                    lineage=json.dumps(
                        [
                            f"binance:{snapshot.symbol}",
                            "api/v3/depth",
                            "api/v3/ticker/24hr",
                            LIVE_FEATURE_ID,
                        ]
                    ),
                )
            )

            replay_points = []
            for point in snapshot.replay_points:
                replay_points.append(
                    ReplayPointModel(
                        feature_id=point.feature_id,
                        timestamp=point.timestamp,
                        expected_value=point.expected_value,
                        actual_value=point.actual_value,
                        trust_score=max(
                            0.0,
                            round(
                                weighted_trust
                                - min((abs(point.actual_value - point.expected_value) / max(point.expected_value, 1.0)) * 400, 40),
                                2,
                            ),
                        ),
                        blocked=status == "critical",
                    )
                )
            self.replay_repository.replace_points(LIVE_FEATURE_ID, replay_points)

            if status == "critical":
                self.incident_repository.upsert_live_incident(
                    LIVE_INCIDENT_ID,
                    feed_id=feed_id,
                    title="Live Binance feed trust breach",
                    severity=status,
                    status="triage",
                    summary=(
                        f"{self.settings.live_vendor_symbol} freshness {freshness:.1f} and drift score "
                        f"{drift_anomaly_score:.1f} pushed trust to {weighted_trust:.1f}."
                    ),
                    impacted_features=["Order Imbalance Regime"],
                )
            else:
                self.incident_repository.resolve_live_incident(LIVE_INCIDENT_ID)

            self.session.commit()
            print(
                "live_refresh_completed",
                {
                    "feed_id": feed_id,
                    "symbol": snapshot.symbol,
                    "trust": weighted_trust,
                    "latency_seconds": snapshot.latency_seconds,
                    "schema_version": snapshot.schema_version,
                },
            )
            return self.ingestion_repository.mark_completed(run.id, record_count=len(replay_points))
        except Exception as exc:
            self.session.rollback()
            latest_snapshot = self.feed_repository.get_latest_snapshot_or_none(feed_id)
            self.ingestion_repository.mark_failed(run.id, str(exc)[:500])
            print(
                "live_refresh_failed",
                {
                    "feed_id": feed_id,
                    "symbol": self.settings.live_vendor_symbol,
                    "data_mode": self.settings.data_mode,
                    "error": str(exc),
                    "fallback_snapshot": latest_snapshot is not None,
                },
            )
            self.incident_repository.upsert_live_incident(
                LIVE_INCIDENT_ID,
                feed_id=feed_id,
                title="Live Binance feed refresh failed",
                severity="critical",
                status="triage",
                summary=(
                    f"Unable to refresh {self.settings.live_vendor_symbol} from Binance: {str(exc)[:180]}"
                ),
                impacted_features=["Order Imbalance Regime"],
            )
            self.feed_repository.update_status(feed_id, "warning")
            self.session.commit()
            if latest_snapshot is not None:
                return run
            raise
