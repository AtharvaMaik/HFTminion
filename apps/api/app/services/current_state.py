from __future__ import annotations

import json
from datetime import datetime, timedelta

from ..repositories import (
    FeatureRepository,
    FeedRepository,
    IncidentRepository,
    MetricsRepository,
    ReplayRepository,
)
from .live_vendor import LiveFeedRefreshService
from ..schemas import (
    FeatureDefinition,
    FeatureSnapshot,
    FeedDefinition,
    FeedHealth,
    IncidentRecord,
    OverviewMetric,
    OverviewResponse,
    ReplayPoint,
    ReplayResponse,
    ReliabilitySnapshot,
)


def _serialize_feed(feed) -> FeedDefinition:
    return FeedDefinition(
        id=feed.id,
        name=feed.name,
        vendor=feed.vendor,
        region=feed.region,
        feed_class=feed.feed_class,
        freshness_sla_seconds=feed.freshness_sla_seconds,
        coverage_target_pct=feed.coverage_target_pct,
        status=feed.status,
    )


def _serialize_snapshot(snapshot) -> ReliabilitySnapshot:
    return ReliabilitySnapshot(
        timestamp=snapshot.computed_at,
        freshness=snapshot.freshness,
        completeness=snapshot.completeness,
        schema_stability=snapshot.schema_stability,
        entity_coverage=snapshot.entity_coverage,
        revision_rate=snapshot.revision_rate,
        drift_anomaly_score=snapshot.drift_anomaly_score,
        weighted_trust_score=snapshot.weighted_trust_score,
        status=snapshot.status,
    )


def _serialize_incident(incident) -> IncidentRecord:
    return IncidentRecord(
        id=incident.id,
        title=incident.title,
        feed_id=incident.feed_id,
        severity=incident.severity,
        status=incident.status,
        started_at=incident.started_at,
        acknowledged=incident.acknowledged,
        summary=incident.summary,
        impacted_features=json.loads(incident.impacted_features),
    )


class CurrentStateService:
    def __init__(self, session):
        self.feed_repository = FeedRepository(session)
        self.feature_repository = FeatureRepository(session)
        self.incident_repository = IncidentRepository(session)
        self.metrics_repository = MetricsRepository(session)
        self.replay_repository = ReplayRepository(session)
        self.live_refresh = LiveFeedRefreshService(session)

    def list_feeds(self) -> list[FeedDefinition]:
        if self.live_refresh.is_live_mode_enabled():
            self.live_refresh.refresh_registered_live_feeds()
        return [_serialize_feed(feed) for feed in self.feed_repository.list_feeds()]

    def get_feed_health(self, feed_id: str) -> FeedHealth:
        self.live_refresh.ensure_feed_is_current(feed_id)
        feed = self.feed_repository.get_feed(feed_id)
        snapshot = self.feed_repository.get_latest_snapshot(feed_id)
        incidents = [
            incident
            for incident in self.incident_repository.list_incidents()
            if incident.feed_id == feed_id
        ]
        return FeedHealth(
            feed=_serialize_feed(feed),
            latest_snapshot=_serialize_snapshot(snapshot),
            latency_seconds=snapshot.latency_seconds,
            schema_version=snapshot.schema_version,
            incident_count=len(incidents),
        )

    def list_features(self) -> list[FeatureDefinition]:
        return [
            FeatureDefinition(
                id=feature.id,
                name=feature.name,
                feed_id=feature.feed_id,
                description=feature.description,
                owner=feature.owner,
            )
            for feature in self.feature_repository.list_features()
        ]

    def get_feature_snapshot(self, feature_id: str) -> FeatureSnapshot:
        feature = self.feature_repository.get_feature(feature_id)
        if self.live_refresh.is_live_feed(feature.feed_id):
            self.live_refresh.ensure_feed_is_current(feature.feed_id)
        snapshot = self.feature_repository.get_latest_snapshot(feature_id)
        return FeatureSnapshot(
            feature_id=feature.id,
            feature_name=feature.name,
            latest_value=snapshot.latest_value,
            reliability=_serialize_snapshot(snapshot.feed_snapshot),
            lineage=json.loads(snapshot.lineage),
        )

    def list_incidents(self) -> list[IncidentRecord]:
        if self.live_refresh.is_live_mode_enabled():
            self.live_refresh.refresh_registered_live_feeds()
        return [_serialize_incident(incident) for incident in self.incident_repository.list_incidents()]

    def metrics_overview(self) -> OverviewResponse:
        if self.live_refresh.is_live_mode_enabled():
            self.live_refresh.refresh_registered_live_feeds()
        incidents = [_serialize_incident(incident) for incident in self.metrics_repository.list_incidents()]
        snapshots = self.metrics_repository.list_latest_snapshots()
        average_trust = round(sum(snapshot.weighted_trust_score for snapshot in snapshots) / max(1, len(snapshots)), 1)
        now = datetime.utcnow()
        trend = [
            ((now - timedelta(hours=idx)).strftime("%H:%M"), score)
            for idx, score in enumerate([93, 92, 91, 90, 88, 87, 84, 82, 80, 78, 74, 71])
        ][::-1]

        return OverviewResponse(
            metrics=[
                OverviewMetric(label="Tracked feeds", value="18", delta="+2 week/week", tone="cyan"),
                OverviewMetric(label="Healthy trust", value=f"{average_trust:.1f}%", delta="+4.2 pts", tone="emerald"),
                OverviewMetric(
                    label="Active incidents",
                    value=str(len([incident for incident in incidents if incident.status != "resolved"])),
                    delta="-1 since open",
                    tone="amber",
                ),
                OverviewMetric(
                    label="Blocked features",
                    value=str(self.metrics_repository.count_blocked_features()),
                    delta="news_event_feed",
                    tone="red",
                ),
            ],
            feeds_by_status={
                "healthy": sum(1 for snapshot in snapshots if snapshot.status == "healthy"),
                "warning": sum(1 for snapshot in snapshots if snapshot.status == "warning"),
                "critical": sum(1 for snapshot in snapshots if snapshot.status == "critical"),
            },
            trust_timeseries=trend,
            incidents=incidents,
        )

    def replay(self, feature_id: str) -> ReplayResponse:
        feature = self.feature_repository.get_feature(feature_id)
        if self.live_refresh.is_live_feed(feature.feed_id):
            self.live_refresh.ensure_feed_is_current(feature.feed_id)
        points = self.replay_repository.list_points(feature_id)
        return ReplayResponse(
            feature_id=feature.id,
            feature_name=feature.name,
            points=[
                ReplayPoint(
                    timestamp=point.timestamp,
                    expected_value=point.expected_value,
                    actual_value=point.actual_value,
                    trust_score=point.trust_score,
                    blocked=point.blocked,
                )
                for point in points
            ],
        )
