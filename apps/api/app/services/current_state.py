from __future__ import annotations

from collections import defaultdict
import json
from datetime import datetime, timedelta, timezone

from ..repositories import (
    FeatureRepository,
    FeedRepository,
    IncidentRepository,
    MetricsRepository,
    ReplayRepository,
)
from .live_vendor import LiveFeedRefreshService
from .live_registry import LIVE_FEED_IDS, LIVE_FEATURE_IDS
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

    def _is_live_mode_enabled(self) -> bool:
        return self.live_refresh.is_live_mode_enabled()

    def _live_feed_id_set(self) -> set[str]:
        return set(LIVE_FEED_IDS)

    def _live_feature_id_set(self) -> set[str]:
        return set(LIVE_FEATURE_IDS)

    def list_feeds(self) -> list[FeedDefinition]:
        if self._is_live_mode_enabled():
            self.live_refresh.refresh_registered_live_feeds()
        feeds = self.feed_repository.list_feeds()
        if self._is_live_mode_enabled():
            live_feed_ids = self._live_feed_id_set()
            feeds = [feed for feed in feeds if feed.id in live_feed_ids]
        return [_serialize_feed(feed) for feed in feeds]

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
        features = self.feature_repository.list_features()
        if self._is_live_mode_enabled():
            live_feature_ids = self._live_feature_id_set()
            features = [feature for feature in features if feature.id in live_feature_ids]
        return [
            FeatureDefinition(
                id=feature.id,
                name=feature.name,
                feed_id=feature.feed_id,
                description=feature.description,
                owner=feature.owner,
            )
            for feature in features
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
        if self._is_live_mode_enabled():
            self.live_refresh.refresh_registered_live_feeds()
        incidents = self.incident_repository.list_incidents()
        if self._is_live_mode_enabled():
            live_feed_ids = self._live_feed_id_set()
            incidents = [incident for incident in incidents if incident.feed_id in live_feed_ids]
        return [_serialize_incident(incident) for incident in incidents]

    def _build_trust_timeseries(self, live_feed_ids: set[str] | None = None) -> list[tuple[str, float]]:
        since = datetime.utcnow().replace(microsecond=0) - timedelta(hours=24)
        recent_snapshots = self.metrics_repository.list_recent_snapshots(
            since,
            sorted(live_feed_ids) if live_feed_ids is not None else None,
        )

        if not recent_snapshots:
            latest_snapshots = self.metrics_repository.list_latest_snapshots()
            if live_feed_ids is not None:
                latest_snapshots = [
                    snapshot for snapshot in latest_snapshots if snapshot.feed_id in live_feed_ids
                ]
            if not latest_snapshots:
                return []
            latest_timestamp = max(snapshot.computed_at for snapshot in latest_snapshots)
            latest_average = round(
                sum(snapshot.weighted_trust_score for snapshot in latest_snapshots)
                / len(latest_snapshots),
                1,
            )
            return [(latest_timestamp.replace(tzinfo=timezone.utc).isoformat(), latest_average)]

        buckets: dict[datetime, list[float]] = defaultdict(list)
        for snapshot in recent_snapshots:
            bucket_second = snapshot.computed_at.second - (snapshot.computed_at.second % 5)
            bucket_time = snapshot.computed_at.replace(second=bucket_second, microsecond=0)
            buckets[bucket_time].append(snapshot.weighted_trust_score)

        trend = sorted(
            (
                bucket_time.replace(tzinfo=timezone.utc).isoformat(),
                round(sum(scores) / len(scores), 1),
            )
            for bucket_time, scores in buckets.items()
        )[-12:]
        return trend

    def metrics_overview(self) -> OverviewResponse:
        if self._is_live_mode_enabled():
            self.live_refresh.refresh_registered_live_feeds()
        live_mode = self._is_live_mode_enabled()
        incidents = self.metrics_repository.list_incidents()
        snapshots = self.metrics_repository.list_latest_snapshots()
        tracked_feeds_value = "18"
        blocked_features_count = self.metrics_repository.count_blocked_features()

        if live_mode:
            live_feed_ids = self._live_feed_id_set()
            live_feature_ids = self._live_feature_id_set()
            incidents = [incident for incident in incidents if incident.feed_id in live_feed_ids]
            snapshots = [snapshot for snapshot in snapshots if snapshot.feed_id in live_feed_ids]
            tracked_feeds_value = str(len(snapshots))
            blocked_features_count = sum(
                1
                for feature_id in live_feature_ids
                if self.feature_repository.get_latest_snapshot(feature_id).blocked
            )

        serialized_incidents = [_serialize_incident(incident) for incident in incidents]
        average_trust = round(sum(snapshot.weighted_trust_score for snapshot in snapshots) / max(1, len(snapshots)), 1)
        trend = self._build_trust_timeseries(live_feed_ids if live_mode else None)

        return OverviewResponse(
            metrics=[
                OverviewMetric(label="Tracked feeds", value=tracked_feeds_value, delta="+2 week/week", tone="cyan"),
                OverviewMetric(label="Healthy trust", value=f"{average_trust:.1f}%", delta="+4.2 pts", tone="emerald"),
                OverviewMetric(
                    label="Active incidents",
                    value=str(len([incident for incident in serialized_incidents if incident.status != "resolved"])),
                    delta="-1 since open",
                    tone="amber",
                ),
                OverviewMetric(
                    label="Blocked features",
                    value=str(blocked_features_count),
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
            incidents=serialized_incidents,
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
