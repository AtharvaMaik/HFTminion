from __future__ import annotations

from datetime import datetime, timedelta

from .connectors import generate_deliveries
from .scoring import ReliabilityInputs, classify_status, compute_weighted_trust_score

from .schemas import (
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


FEEDS = [
    FeedDefinition(
        id="feed-binance-agg",
        name="BINANCE_USDT_AGG_V2",
        vendor="Binance",
        region="ap-south-1",
        feed_class="traffic_proxy",
        freshness_sla_seconds=18,
        coverage_target_pct=99.2,
        status="healthy",
    ),
    FeedDefinition(
        id="feed-economic-calendar",
        name="ZZ_ECONOMIC_CALENDAR_ALPHA",
        vendor="Macro Calendar Source",
        region="us-east-1",
        feed_class="macro_calendar_feed",
        freshness_sla_seconds=300,
        coverage_target_pct=96.0,
        status="warning",
    ),
    FeedDefinition(
        id="feed-public-news",
        name="PUBLIC_NEWS_ALPHA",
        vendor="Public News Source",
        region="eu-west-1",
        feed_class="news_event_feed",
        freshness_sla_seconds=45,
        coverage_target_pct=98.5,
        status="critical",
    ),
]


FEATURES = [
    FeatureDefinition(
        id="feat-order-imbalance",
        name="Order Imbalance Regime",
        feed_id="feed-binance-agg",
        description="Derived intraday regime score based on trade imbalance and spread pressure.",
        owner="research-market-micro",
    ),
    FeatureDefinition(
        id="feat-economic-event-pressure",
        name="Economic Event Pressure",
        feed_id="feed-economic-calendar",
        description="Macro calendar event pressure based on release timing, surprise magnitude, and market sensitivity.",
        owner="research-consumer",
    ),
    FeatureDefinition(
        id="feat-headline-velocity",
        name="Headline Velocity",
        feed_id="feed-public-news",
        description="Low-latency event polarity for macro and geopolitical triggers.",
        owner="research-macro",
    ),
]


def _snapshot(
    freshness: float,
    completeness: float,
    schema_stability: float,
    entity_coverage: float,
    revision_rate: float,
    drift_anomaly_score: float,
) -> ReliabilitySnapshot:
    weighted = compute_weighted_trust_score(
        ReliabilityInputs(
            freshness=freshness,
            completeness=completeness,
            schema_stability=schema_stability,
            entity_coverage=entity_coverage,
            revision_rate=revision_rate,
            drift_anomaly_score=drift_anomaly_score,
        )
    )
    return ReliabilitySnapshot(
        timestamp=datetime.utcnow().replace(microsecond=0),
        freshness=freshness,
        completeness=completeness,
        schema_stability=schema_stability,
        entity_coverage=entity_coverage,
        revision_rate=revision_rate,
        drift_anomaly_score=drift_anomaly_score,
        weighted_trust_score=weighted,
        status=classify_status(weighted),
    )


SNAPSHOTS = {
    "feed-binance-agg": _snapshot(96, 98, 94, 95, 89, 91),
    "feed-economic-calendar": _snapshot(72, 81, 78, 76, 69, 71),
    "feed-public-news": _snapshot(39, 62, 55, 51, 44, 42),
}


INCIDENTS = [
    IncidentRecord(
        id="inc-live-feed-economic-calendar",
        title="Revision burst exceeded daily baseline",
        feed_id="feed-economic-calendar",
        severity="warning",
        status="investigating",
        started_at=datetime.utcnow().replace(microsecond=0) - timedelta(hours=3, minutes=14),
        acknowledged=True,
        summary="Vendor backfill revisions spiked 3.6x above the expected rate.",
        impacted_features=["Economic Event Pressure"],
    ),
    IncidentRecord(
        id="inc-live-feed-public-news",
        title="Macro event feed staleness breach",
        feed_id="feed-public-news",
        severity="critical",
        status="triage",
        started_at=datetime.utcnow().replace(microsecond=0) - timedelta(minutes=47),
        acknowledged=False,
        summary="Latency breached the 45 second SLA for 7 consecutive windows.",
        impacted_features=["Headline Velocity"],
    ),
]


def list_feeds() -> list[FeedDefinition]:
    return FEEDS


def get_feed_health(feed_id: str) -> FeedHealth:
    feed = next(feed for feed in FEEDS if feed.id == feed_id)
    deliveries = generate_deliveries(feed_id)
    return FeedHealth(
        feed=feed,
        latest_snapshot=SNAPSHOTS[feed_id],
        latency_seconds=max(7, int(feed.freshness_sla_seconds * (100 - SNAPSHOTS[feed_id].freshness) / 100) + 8),
        schema_version=deliveries[0].schema_version,
        incident_count=sum(1 for incident in INCIDENTS if incident.feed_id == feed_id),
    )


def list_features() -> list[FeatureDefinition]:
    return FEATURES


def get_feature_snapshot(feature_id: str) -> FeatureSnapshot:
    feature = next(feature for feature in FEATURES if feature.id == feature_id)
    sample_values = {
        "feat-order-imbalance": 1.24,
        "feat-economic-event-pressure": -0.42,
        "feat-headline-velocity": -1.88,
    }
    return FeatureSnapshot(
        feature_id=feature.id,
        feature_name=feature.name,
        latest_value=sample_values[feature_id],
        reliability=SNAPSHOTS[feature.feed_id],
        lineage=[feature.feed_id, "normalizer.v2", feature.id],
    )


def list_incidents() -> list[IncidentRecord]:
    return INCIDENTS


def acknowledge_incident(incident_id: str) -> IncidentRecord:
    incident = next(incident for incident in INCIDENTS if incident.id == incident_id)
    incident.acknowledged = True
    return incident


def metrics_overview() -> OverviewResponse:
    trend = [
        ((datetime.utcnow() - timedelta(hours=idx)).strftime("%H:%M"), score)
        for idx, score in enumerate([93, 92, 91, 90, 88, 87, 84, 82, 80, 78, 74, 71])
    ][::-1]
    return OverviewResponse(
        metrics=[
            OverviewMetric(label="Tracked feeds", value="18", delta="+2 week/week", tone="cyan"),
            OverviewMetric(label="Healthy trust", value="83.7%", delta="+4.2 pts", tone="emerald"),
            OverviewMetric(label="Active incidents", value="2", delta="-1 since open", tone="amber"),
            OverviewMetric(label="Blocked features", value="1", delta="news_event_feed", tone="red"),
        ],
        feeds_by_status={
            "healthy": sum(1 for feed in FEEDS if feed.status == "healthy"),
            "warning": sum(1 for feed in FEEDS if feed.status == "warning"),
            "critical": sum(1 for feed in FEEDS if feed.status == "critical"),
        },
        trust_timeseries=trend,
        incidents=INCIDENTS,
    )


def replay(feature_id: str) -> ReplayResponse:
    feature = next(feature for feature in FEATURES if feature.id == feature_id)
    points = [
        ReplayPoint(
            timestamp=datetime.utcnow().replace(microsecond=0) - timedelta(minutes=10 * idx),
            expected_value=1.24 - (idx * 0.02),
            actual_value=1.19 - (idx * 0.07),
            trust_score=max(38, 86 - idx * 4),
            blocked=idx > 6,
        )
        for idx in range(10)
    ][::-1]
    return ReplayResponse(feature_id=feature.id, feature_name=feature.name, points=points)

