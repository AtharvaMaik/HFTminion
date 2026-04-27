from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

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


@runtime_checkable
class LiveConnector(Protocol):
    feed_id: str
    source_name: str
    primary_feature_id: str
    schema_version: str

    def fetch_snapshot(self, freshness_sla_seconds: int) -> LiveConnectorSnapshot:
        ...


def get_live_connectors() -> dict[str, LiveConnector]:
    from .live_vendor import BinanceSpotConnector

    connector = BinanceSpotConnector()
    return {connector.feed_id: connector}
