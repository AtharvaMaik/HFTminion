from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class FeedModel(Base):
    __tablename__ = "feeds"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str] = mapped_column(String(64), nullable=False)
    feed_class: Mapped[str] = mapped_column(String(64), nullable=False)
    freshness_sla_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    coverage_target_pct: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)


class FeatureModel(Base):
    __tablename__ = "features"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    feed_id: Mapped[str] = mapped_column(ForeignKey("feeds.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)

    feed: Mapped[FeedModel] = relationship()


class FeedSnapshotModel(Base):
    __tablename__ = "feed_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feed_id: Mapped[str] = mapped_column(ForeignKey("feeds.id"), nullable=False, index=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    freshness: Mapped[float] = mapped_column(Float, nullable=False)
    completeness: Mapped[float] = mapped_column(Float, nullable=False)
    schema_stability: Mapped[float] = mapped_column(Float, nullable=False)
    entity_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    revision_rate: Mapped[float] = mapped_column(Float, nullable=False)
    drift_anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    weighted_trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    latency_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)

    feed: Mapped[FeedModel] = relationship()


class FeatureSnapshotModel(Base):
    __tablename__ = "feature_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feature_id: Mapped[str] = mapped_column(ForeignKey("features.id"), nullable=False, index=True)
    feed_snapshot_id: Mapped[int] = mapped_column(ForeignKey("feed_snapshots.id"), nullable=False, index=True)
    source_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    latest_value: Mapped[float] = mapped_column(Float, nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    lineage: Mapped[str] = mapped_column(Text, nullable=False)

    feature: Mapped[FeatureModel] = relationship()
    feed_snapshot: Mapped[FeedSnapshotModel] = relationship()


class IncidentModel(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    feed_id: Mapped[str] = mapped_column(ForeignKey("feeds.id"), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    impacted_features: Mapped[str] = mapped_column(Text, nullable=False)

    feed: Mapped[FeedModel] = relationship()


class IncidentEventModel(Base):
    __tablename__ = "incident_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)


class ReplayPointModel(Base):
    __tablename__ = "replay_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feature_id: Mapped[str] = mapped_column(ForeignKey("features.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class IngestionRunModel(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    feed_id: Mapped[str] = mapped_column(String(128), nullable=False)
    run_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
