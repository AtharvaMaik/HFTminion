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
from .live_connectors import get_live_connectors


LIVE_FEATURE_ID = "feat-order-imbalance"


def get_live_incident_id(feed_id: str) -> str:
    return f"inc-live-feed-{feed_id.removeprefix('feed-')}"


@dataclass(frozen=True)
class BinanceSnapshot:
    symbol: str
    source_name: str
    source_lineage_prefix: list[str]
    primary_feature_id: str
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
    freshness_score: float | None = None
    completeness_score: float | None = None
    schema_stability_score: float | None = None
    entity_coverage_score: float | None = None
    revision_rate_score: float | None = None
    drift_anomaly_score: float | None = None
    feature_value: float | None = None


class BinanceSpotConnector:
    feed_id = "feed-binance-agg"
    source_name = "Binance"
    primary_feature_id = LIVE_FEATURE_ID
    schema_version = "binance-spot-v3"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.default_symbol = self.settings.live_vendor_symbol

    def _get_json(self, path: str, params: dict[str, str | int]) -> dict | list:
        with httpx.Client(
            base_url=self.settings.live_vendor_base_url,
            timeout=self.settings.live_vendor_timeout_seconds,
        ) as client:
            response = client.get(path, params=params)
            response.raise_for_status()
            return response.json()

    def is_snapshot_schema_current(self, snapshot_schema_version: str) -> bool:
        return snapshot_schema_version == self.schema_version

    def fetch_snapshot(self, _freshness_sla_seconds: int) -> BinanceSnapshot:
        symbol = self.default_symbol
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
                feature_id=self.primary_feature_id,
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
            source_name=self.source_name,
            source_lineage_prefix=[f"binance:{symbol}", "api/v3/depth", "api/v3/ticker/24hr"],
            primary_feature_id=self.primary_feature_id,
            avg_price=avg_price_value,
            last_price=float(ticker["lastPrice"]),
            price_change_pct=float(ticker["priceChangePercent"]),
            latency_seconds=latency_seconds,
            schema_version=self.schema_version,
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
        self.connectors = get_live_connectors()

    def is_live_mode_enabled(self) -> bool:
        return self.settings.data_mode == "live"

    def get_connector_for_feed(self, feed_id: str):
        return self.connectors.get(feed_id)

    def is_live_feed(self, feed_id: str) -> bool:
        return self.is_live_mode_enabled() and self.get_connector_for_feed(feed_id) is not None

    def refresh_registered_live_feeds(self):
        if not self.connectors:
            raise RuntimeError("No live connectors registered")

        latest_run = None
        for feed_id in self.connectors:
            latest_run = self.refresh_live_feed(feed_id)
        return latest_run

    def ensure_feed_is_current(self, feed_id: str) -> None:
        connector = self.get_connector_for_feed(feed_id)
        if not self.is_live_mode_enabled() or connector is None:
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
                connector.is_snapshot_schema_current(latest_snapshot.schema_version)
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
                "source_name": connector.source_name,
                "data_mode": self.settings.data_mode,
            },
        )
        self.refresh_live_feed(feed_id)

    def refresh_live_feed(self, feed_id: str):
        connector = self.get_connector_for_feed(feed_id)
        if connector is None:
            raise KeyError(f"No live connector registered for feed_id={feed_id}")

        feed = self.feed_repository.get_feed(feed_id)
        run = self.ingestion_repository.create_run(feed_id=feed_id, run_type="poll", status="running")
        source_name = connector.source_name
        source_symbol = feed_id
        impacted_feature_name = feed_id

        try:
            snapshot = connector.fetch_snapshot(feed.freshness_sla_seconds)
            source_symbol = snapshot.symbol
            feature_id = connector.primary_feature_id
            feature = self.feature_repository.get_feature(feature_id)
            impacted_feature_name = feature.name

            freshness = getattr(snapshot, "freshness_score", None)
            if freshness is None:
                freshness = max(
                    0.0,
                    min(
                        100.0,
                        round(100 - ((snapshot.latency_seconds / max(1, feed.freshness_sla_seconds)) * 100), 2),
                    ),
                )
            completeness_score = getattr(snapshot, "completeness_score", None)
            completeness = completeness_score if completeness_score is not None else 100.0
            schema_stability_score = getattr(snapshot, "schema_stability_score", None)
            schema_stability = (
                schema_stability_score if schema_stability_score is not None else 100.0
            )
            entity_coverage_score = getattr(snapshot, "entity_coverage_score", None)
            entity_coverage = (
                entity_coverage_score
                if entity_coverage_score is not None
                else min(100.0, round((snapshot.trade_count / 1000) * 100, 2))
            )
            revision_rate_score = getattr(snapshot, "revision_rate_score", None)
            revision_rate = revision_rate_score if revision_rate_score is not None else 100.0
            drift_score = getattr(snapshot, "drift_anomaly_score", None)
            drift_anomaly_score = (
                drift_score
                if drift_score is not None
                else max(0.0, round(100 - min(abs(snapshot.price_change_pct) * 4, 70), 2))
            )
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
            feature_value = getattr(snapshot, "feature_value", None)
            if feature_value is None:
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
                    feature_id=feature_id,
                    feed_snapshot_id=feed_snapshot.id,
                    source_timestamp=snapshot.computed_at,
                    latest_value=feature_value,
                    trust_score=weighted_trust,
                    blocked=status == "critical",
                    lineage=json.dumps(
                        [*snapshot.source_lineage_prefix, feature_id]
                    ),
                )
            )

            replay_points = []
            for point in snapshot.replay_points:
                replay_points.append(
                    ReplayPointModel(
                        feature_id=feature_id,
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
            self.replay_repository.replace_points(feature_id, replay_points)

            if status == "critical":
                incident_id = get_live_incident_id(feed_id)
                self.incident_repository.upsert_live_incident(
                    incident_id,
                    feed_id=feed_id,
                    title=f"Live {source_name} feed trust breach",
                    severity=status,
                    status="triage",
                summary=(
                    f"{snapshot.symbol} freshness {freshness:.1f} and drift score "
                        f"{drift_anomaly_score:.1f} pushed trust to {weighted_trust:.1f}."
                    ),
                    impacted_features=[feature.name],
                )
            else:
                self.incident_repository.resolve_live_incident(get_live_incident_id(feed_id))

            self.session.commit()
            print(
                "live_refresh_completed",
                {
                    "feed_id": feed_id,
                    "symbol": source_symbol,
                    "source_name": source_name,
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
                    "source_name": source_name,
                    "data_mode": self.settings.data_mode,
                    "error": str(exc),
                    "fallback_snapshot": latest_snapshot is not None,
                },
            )
            self.incident_repository.upsert_live_incident(
                get_live_incident_id(feed_id),
                feed_id=feed_id,
                title=f"Live {source_name} feed refresh failed",
                severity="critical",
                status="triage",
                summary=(
                    f"Unable to refresh {source_symbol} from {source_name}: {str(exc)[:180]}"
                ),
                impacted_features=[impacted_feature_name],
            )
            self.feed_repository.update_status(feed_id, "warning")
            self.session.commit()
            if latest_snapshot is not None:
                return run
            raise
