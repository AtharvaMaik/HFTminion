from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Protocol, runtime_checkable
import xml.etree.ElementTree as ET

import httpx

from ..config import get_settings
from ..models import ReplayPointModel


@dataclass(frozen=True)
class LiveConnectorSnapshot:
    source_name: str
    source_lineage_prefix: list[str]
    primary_feature_id: str
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
    freshness_score: float | None = None
    completeness_score: float | None = None
    schema_stability_score: float | None = None
    entity_coverage_score: float | None = None
    revision_rate_score: float | None = None
    drift_anomaly_score: float | None = None
    feature_value: float | None = None


@runtime_checkable
class LiveConnector(Protocol):
    feed_id: str
    source_name: str
    primary_feature_id: str
    schema_version: str

    def fetch_snapshot(self, freshness_sla_seconds: int) -> LiveConnectorSnapshot:
        ...

    def is_snapshot_schema_current(self, snapshot_schema_version: str) -> bool:
        ...


class PublicNewsRssConnector:
    feed_id = "feed-public-news"
    source_name = "Public News RSS"
    primary_feature_id = "feat-headline-velocity"
    schema_version = "rss-*"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.source_url = self.settings.live_public_news_rss_url

    def _get_feed_xml(self) -> str:
        with httpx.Client(timeout=self.settings.live_vendor_timeout_seconds, follow_redirects=True) as client:
            response = client.get(self.source_url)
            response.raise_for_status()
            return response.text

    def _iter_items(self, root: ET.Element) -> list[ET.Element]:
        if root.tag.endswith("feed"):
            return root.findall("{*}entry")
        return root.findall("./channel/item")

    def _read_item(self, item: ET.Element) -> tuple[str | None, datetime | None]:
        title = item.findtext("title") or item.findtext("{*}title")
        published_text = (
            item.findtext("pubDate")
            or item.findtext("{*}published")
            or item.findtext("{*}updated")
        )
        if published_text is None:
            return title, None

        published_at: datetime | None = None
        try:
            published_at = parsedate_to_datetime(published_text)
        except (TypeError, ValueError, IndexError):
            try:
                published_at = datetime.fromisoformat(published_text.replace("Z", "+00:00"))
            except ValueError:
                return title, None

        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        return title, published_at.astimezone(timezone.utc)

    def fetch_snapshot(self, freshness_sla_seconds: int) -> LiveConnectorSnapshot:
        xml_text = self._get_feed_xml()
        root = ET.fromstring(xml_text)
        schema_version = f"rss-{root.attrib.get('version', 'atom')}"
        computed_at = datetime.utcnow().replace(microsecond=0)
        items = self._iter_items(root)
        total_items = len(items)
        parse_successes = 0
        continuity_successes = 0
        previous_parsed = False
        parsed_entries: list[tuple[str, datetime]] = []

        for item in items:
            title, published_at = self._read_item(item)
            parsed = bool(title and published_at)
            if parsed:
                parse_successes += 1
                parsed_entries.append((title.strip(), published_at.replace(tzinfo=None, microsecond=0)))
            if parsed and previous_parsed:
                continuity_successes += 1
            previous_parsed = parsed

        if not parsed_entries:
            raise ValueError("RSS feed returned no parseable items")

        parsed_entries.sort(key=lambda entry: entry[1])
        latest_published_at = parsed_entries[-1][1]
        latency_seconds = max(0, int((computed_at - latest_published_at).total_seconds()))
        lookback_start = computed_at - timedelta(hours=1)
        recent_entries = [entry for entry in parsed_entries if entry[1] >= lookback_start]
        recent_count = len(recent_entries)
        headline_count = len(parsed_entries)
        completeness = round((parse_successes / max(total_items, 1)) * 100, 2)
        schema_stability = round((continuity_successes / max(total_items - 1, 1)) * 100, 2) if total_items > 1 else completeness
        freshness = max(
            0.0,
            min(100.0, round(100 - ((latency_seconds / max(1, freshness_sla_seconds)) * 100), 2)),
        )
        entity_coverage = min(100.0, round((headline_count / 25) * 100, 2))
        revision_rate = min(100.0, round((recent_count / max(headline_count, 1)) * 100, 2))
        drift_anomaly_score = max(0.0, round(100 - min(latency_seconds / 6, 80), 2))
        feature_value = round(recent_count / max(headline_count, 1), 4)

        replay_points = [
            ReplayPointModel(
                feature_id=self.primary_feature_id,
                timestamp=published_at,
                expected_value=feature_value,
                actual_value=round(1.0 if published_at >= lookback_start else 0.0, 4),
                trust_score=max(0.0, round(freshness - abs(feature_value - (1.0 if published_at >= lookback_start else 0.0)) * 100, 2)),
                blocked=False,
            )
            for _, published_at in parsed_entries[-10:]
        ]

        return LiveConnectorSnapshot(
            source_name=self.source_name,
            source_lineage_prefix=[
                "source:public-news-rss",
                "rss:item-count",
            ],
            primary_feature_id=self.primary_feature_id,
            symbol="public-news-rss",
            avg_price=float(headline_count),
            last_price=float(recent_count),
            price_change_pct=0.0,
            latency_seconds=latency_seconds,
            schema_version=schema_version,
            bid_qty=float(recent_count),
            ask_qty=float(max(headline_count - recent_count, 0)),
            trade_count=headline_count,
            quote_volume=float(total_items),
            freshness_score=freshness,
            completeness_score=completeness,
            schema_stability_score=schema_stability,
            entity_coverage_score=entity_coverage,
            revision_rate_score=revision_rate,
            drift_anomaly_score=drift_anomaly_score,
            feature_value=feature_value,
            computed_at=computed_at,
            replay_points=replay_points,
        )

    def is_snapshot_schema_current(self, snapshot_schema_version: str) -> bool:
        return snapshot_schema_version.startswith("rss-")


def get_live_connectors() -> dict[str, LiveConnector]:
    from .live_vendor import BinanceSpotConnector

    connectors = [
        BinanceSpotConnector(),
        PublicNewsRssConnector(),
    ]
    return {connector.feed_id: connector for connector in connectors}
