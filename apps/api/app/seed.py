from __future__ import annotations

from datetime import datetime
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from .data import FEATURES, FEEDS, INCIDENTS, SNAPSHOTS, replay
from .models import (
    Base,
    FeatureModel,
    FeatureSnapshotModel,
    FeedModel,
    FeedSnapshotModel,
    IncidentModel,
    ReplayPointModel,
)
from .connectors import generate_deliveries


def initialize_database(engine) -> None:
    Base.metadata.create_all(engine)


def seed_database(session: Session) -> None:
    existing_feed = session.scalar(select(FeedModel.id).limit(1))
    if existing_feed is not None:
        return

    for feed in FEEDS:
        session.add(
            FeedModel(
                id=feed.id,
                name=feed.name,
                vendor=feed.vendor,
                region=feed.region,
                feed_class=feed.feed_class,
                freshness_sla_seconds=feed.freshness_sla_seconds,
                coverage_target_pct=feed.coverage_target_pct,
                status=feed.status,
            )
        )

    for feature in FEATURES:
        session.add(
            FeatureModel(
                id=feature.id,
                name=feature.name,
                feed_id=feature.feed_id,
                description=feature.description,
                owner=feature.owner,
            )
        )

    session.flush()

    snapshot_ids: dict[str, int] = {}
    for feed in FEEDS:
        snapshot = SNAPSHOTS[feed.id]
        deliveries = generate_deliveries(feed.id)
        feed_snapshot = FeedSnapshotModel(
            feed_id=feed.id,
            computed_at=snapshot.timestamp,
            freshness=snapshot.freshness,
            completeness=snapshot.completeness,
            schema_stability=snapshot.schema_stability,
            entity_coverage=snapshot.entity_coverage,
            revision_rate=snapshot.revision_rate,
            drift_anomaly_score=snapshot.drift_anomaly_score,
            weighted_trust_score=snapshot.weighted_trust_score,
            status=snapshot.status,
            latency_seconds=max(7, int(feed.freshness_sla_seconds * (100 - snapshot.freshness) / 100) + 8),
            schema_version=deliveries[0].schema_version,
        )
        session.add(feed_snapshot)
        session.flush()
        snapshot_ids[feed.id] = feed_snapshot.id

    feature_values = {
        "feat-order-imbalance": 1.24,
        "feat-store-intent": -0.42,
        "feat-news-sentiment": -1.88,
    }
    for feature in FEATURES:
        feature_snapshot = FeatureSnapshotModel(
            feature_id=feature.id,
            feed_snapshot_id=snapshot_ids[feature.feed_id],
            source_timestamp=datetime.utcnow().replace(microsecond=0),
            latest_value=feature_values[feature.id],
            trust_score=SNAPSHOTS[feature.feed_id].weighted_trust_score,
            blocked=feature.id == "feat-news-sentiment",
            lineage=json.dumps([feature.feed_id, "normalizer.v2", feature.id]),
        )
        session.add(feature_snapshot)

    for incident in INCIDENTS:
        session.add(
            IncidentModel(
                id=incident.id,
                title=incident.title,
                feed_id=incident.feed_id,
                severity=incident.severity,
                status=incident.status,
                started_at=incident.started_at,
                acknowledged=incident.acknowledged,
                summary=incident.summary,
                impacted_features=json.dumps(incident.impacted_features),
            )
        )

    for feature in FEATURES:
        replay_response = replay(feature.id)
        for point in replay_response.points:
            session.add(
                ReplayPointModel(
                    feature_id=feature.id,
                    timestamp=point.timestamp,
                    expected_value=point.expected_value,
                    actual_value=point.actual_value,
                    trust_score=point.trust_score,
                    blocked=point.blocked,
                )
            )

    session.commit()
