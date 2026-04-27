from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from random import Random


@dataclass(frozen=True)
class SyntheticDelivery:
    feed_id: str
    received_at: datetime
    payload_size_bytes: int
    completeness_pct: float
    schema_version: str
    revision_flag: bool


def generate_deliveries(feed_id: str, seed: int = 7) -> list[SyntheticDelivery]:
    random = Random(seed)
    now = datetime.utcnow().replace(microsecond=0)
    deliveries: list[SyntheticDelivery] = []
    for offset in range(24):
        completeness = 97.0 - random.randint(0, 8)
        if offset in {6, 11}:
            completeness -= 18
        deliveries.append(
            SyntheticDelivery(
                feed_id=feed_id,
                received_at=now - timedelta(hours=offset),
                payload_size_bytes=random.randint(1200, 9800),
                completeness_pct=max(40.0, completeness),
                schema_version="2.3.1" if offset > 4 else "2.4.0",
                revision_flag=offset in {3, 4, 12},
            )
        )
    return deliveries
