from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ReliabilityStatus = Literal["healthy", "warning", "critical"]
IncidentStatus = Literal["triage", "investigating", "resolved"]
FeedClass = Literal["traffic_proxy", "macro_calendar_feed", "news_event_feed"]


class FeedDefinition(BaseModel):
    id: str
    name: str
    vendor: str
    region: str
    feed_class: FeedClass
    freshness_sla_seconds: int
    coverage_target_pct: float
    status: ReliabilityStatus


class ReliabilitySnapshot(BaseModel):
    timestamp: datetime
    freshness: float = Field(ge=0, le=100)
    completeness: float = Field(ge=0, le=100)
    schema_stability: float = Field(ge=0, le=100)
    entity_coverage: float = Field(ge=0, le=100)
    revision_rate: float = Field(ge=0, le=100)
    drift_anomaly_score: float = Field(ge=0, le=100)
    weighted_trust_score: float = Field(ge=0, le=100)
    status: ReliabilityStatus


class FeedHealth(BaseModel):
    feed: FeedDefinition
    latest_snapshot: ReliabilitySnapshot
    latency_seconds: int
    schema_version: str
    incident_count: int


class FeatureDefinition(BaseModel):
    id: str
    name: str
    feed_id: str
    description: str
    owner: str


class FeatureSnapshot(BaseModel):
    feature_id: str
    feature_name: str
    latest_value: float
    reliability: ReliabilitySnapshot
    lineage: list[str]


class IncidentRecord(BaseModel):
    id: str
    title: str
    feed_id: str
    severity: ReliabilityStatus
    status: IncidentStatus
    started_at: datetime
    acknowledged: bool
    summary: str
    impacted_features: list[str]


class OverviewMetric(BaseModel):
    label: str
    value: str
    delta: str
    tone: Literal["cyan", "emerald", "amber", "red"]


class OverviewResponse(BaseModel):
    metrics: list[OverviewMetric]
    feeds_by_status: dict[str, int]
    trust_timeseries: list[tuple[str, float]]
    incidents: list[IncidentRecord]


class ReplayPoint(BaseModel):
    timestamp: datetime
    expected_value: float
    actual_value: float
    trust_score: float
    blocked: bool


class ReplayResponse(BaseModel):
    feature_id: str
    feature_name: str
    points: list[ReplayPoint]


class AcknowledgeIncidentRequest(BaseModel):
    acknowledged: bool = True

