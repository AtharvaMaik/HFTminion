from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260427_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feeds",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("vendor", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=64), nullable=False),
        sa.Column("feed_class", sa.String(length=64), nullable=False),
        sa.Column("freshness_sla_seconds", sa.Integer(), nullable=False),
        sa.Column("coverage_target_pct", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "features",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("feed_id", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["feed_id"], ["feeds.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_features_feed_id"), "features", ["feed_id"], unique=False)
    op.create_table(
        "feed_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("feed_id", sa.String(length=128), nullable=False),
        sa.Column("computed_at", sa.DateTime(), nullable=False),
        sa.Column("freshness", sa.Float(), nullable=False),
        sa.Column("completeness", sa.Float(), nullable=False),
        sa.Column("schema_stability", sa.Float(), nullable=False),
        sa.Column("entity_coverage", sa.Float(), nullable=False),
        sa.Column("revision_rate", sa.Float(), nullable=False),
        sa.Column("drift_anomaly_score", sa.Float(), nullable=False),
        sa.Column("weighted_trust_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("latency_seconds", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["feed_id"], ["feeds.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_feed_snapshots_computed_at"), "feed_snapshots", ["computed_at"], unique=False)
    op.create_index(op.f("ix_feed_snapshots_feed_id"), "feed_snapshots", ["feed_id"], unique=False)
    op.create_table(
        "incidents",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("feed_id", sa.String(length=128), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("acknowledged", sa.Boolean(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("impacted_features", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["feed_id"], ["feeds.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_incidents_feed_id"), "incidents", ["feed_id"], unique=False)
    op.create_index(op.f("ix_incidents_started_at"), "incidents", ["started_at"], unique=False)
    op.create_table(
        "incident_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("incident_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_incident_events_created_at"), "incident_events", ["created_at"], unique=False)
    op.create_index(op.f("ix_incident_events_incident_id"), "incident_events", ["incident_id"], unique=False)
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("feed_id", sa.String(length=128), nullable=False),
        sa.Column("run_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingestion_runs_started_at"), "ingestion_runs", ["started_at"], unique=False)
    op.create_table(
        "replay_points",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("feature_id", sa.String(length=128), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("expected_value", sa.Float(), nullable=False),
        sa.Column("actual_value", sa.Float(), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=False),
        sa.Column("blocked", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["feature_id"], ["features.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_replay_points_feature_id"), "replay_points", ["feature_id"], unique=False)
    op.create_index(op.f("ix_replay_points_timestamp"), "replay_points", ["timestamp"], unique=False)
    op.create_table(
        "feature_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("feature_id", sa.String(length=128), nullable=False),
        sa.Column("feed_snapshot_id", sa.Integer(), nullable=False),
        sa.Column("source_timestamp", sa.DateTime(), nullable=False),
        sa.Column("latest_value", sa.Float(), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=False),
        sa.Column("blocked", sa.Boolean(), nullable=False),
        sa.Column("lineage", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["feature_id"], ["features.id"]),
        sa.ForeignKeyConstraint(["feed_snapshot_id"], ["feed_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_feature_snapshots_feature_id"), "feature_snapshots", ["feature_id"], unique=False)
    op.create_index(op.f("ix_feature_snapshots_feed_snapshot_id"), "feature_snapshots", ["feed_snapshot_id"], unique=False)
    op.create_index(op.f("ix_feature_snapshots_source_timestamp"), "feature_snapshots", ["source_timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_feature_snapshots_source_timestamp"), table_name="feature_snapshots")
    op.drop_index(op.f("ix_feature_snapshots_feed_snapshot_id"), table_name="feature_snapshots")
    op.drop_index(op.f("ix_feature_snapshots_feature_id"), table_name="feature_snapshots")
    op.drop_table("feature_snapshots")
    op.drop_index(op.f("ix_replay_points_timestamp"), table_name="replay_points")
    op.drop_index(op.f("ix_replay_points_feature_id"), table_name="replay_points")
    op.drop_table("replay_points")
    op.drop_index(op.f("ix_ingestion_runs_started_at"), table_name="ingestion_runs")
    op.drop_table("ingestion_runs")
    op.drop_index(op.f("ix_incident_events_incident_id"), table_name="incident_events")
    op.drop_index(op.f("ix_incident_events_created_at"), table_name="incident_events")
    op.drop_table("incident_events")
    op.drop_index(op.f("ix_incidents_started_at"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_feed_id"), table_name="incidents")
    op.drop_table("incidents")
    op.drop_index(op.f("ix_feed_snapshots_feed_id"), table_name="feed_snapshots")
    op.drop_index(op.f("ix_feed_snapshots_computed_at"), table_name="feed_snapshots")
    op.drop_table("feed_snapshots")
    op.drop_index(op.f("ix_features_feed_id"), table_name="features")
    op.drop_table("features")
    op.drop_table("feeds")
