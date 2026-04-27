from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import data as app_data
from app import seed as app_seed
from app.main import app
from app.models import ReplayPointModel
from app.schemas import FeedDefinition, ReliabilitySnapshot
from app.services.live_vendor import BinanceSnapshot


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test-altdata.db"
    monkeypatch.setenv("DATA_MODE", "database")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def live_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test-live-altdata.db"
    monkeypatch.setenv("DATA_MODE", "live")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("LIVE_REFRESH_WINDOW_SECONDS", "0")

    live_timestamp = datetime.utcnow().replace(microsecond=0)
    live_feeds = app_data.FEEDS + [
        FeedDefinition(
            id="feed-public-news",
            name="PUBLIC_NEWS_ALPHA",
            vendor="EventPulse",
            region="eu-west-1",
            feed_class="news_event_feed",
            freshness_sla_seconds=45,
            coverage_target_pct=98.7,
            status="healthy",
        ),
        FeedDefinition(
            id="feed-economic-calendar",
            name="ZZ_ECONOMIC_CALENDAR_ALPHA",
            vendor="EventPulse",
            region="us-east-1",
            feed_class="news_event_feed",
            freshness_sla_seconds=60,
            coverage_target_pct=97.4,
            status="healthy",
        ),
    ]
    live_snapshots = {
        **app_data.SNAPSHOTS,
        "feed-public-news": ReliabilitySnapshot(
            timestamp=live_timestamp,
            freshness=94.0,
            completeness=97.0,
            schema_stability=95.0,
            entity_coverage=93.0,
            revision_rate=91.0,
            drift_anomaly_score=89.0,
            weighted_trust_score=92.4,
            status="healthy",
        ),
        "feed-economic-calendar": ReliabilitySnapshot(
            timestamp=live_timestamp,
            freshness=91.0,
            completeness=96.0,
            schema_stability=94.0,
            entity_coverage=90.0,
            revision_rate=88.0,
            drift_anomaly_score=87.0,
            weighted_trust_score=90.1,
            status="healthy",
        ),
    }
    monkeypatch.setattr(app_data, "FEEDS", live_feeds)
    monkeypatch.setattr(app_seed, "FEEDS", live_feeds)
    monkeypatch.setattr(app_data, "SNAPSHOTS", live_snapshots)
    monkeypatch.setattr(app_seed, "SNAPSHOTS", live_snapshots)

    def _fake_fetch_snapshot(self, symbol: str, freshness_sla_seconds: int) -> BinanceSnapshot:
        computed_at = datetime.utcnow().replace(microsecond=0)
        return BinanceSnapshot(
            symbol=symbol,
            avg_price=100000.0,
            last_price=100120.0,
            price_change_pct=0.25,
            latency_seconds=2,
            schema_version="binance-spot-v3",
            bid_qty=15.0,
            ask_qty=5.0,
            trade_count=860,
            quote_volume=1200000.0,
            computed_at=computed_at,
            replay_points=[
                ReplayPointModel(
                    feature_id="feat-order-imbalance",
                    timestamp=computed_at - timedelta(minutes=1),
                    expected_value=100000.0,
                    actual_value=99980.0,
                    trust_score=100.0,
                    blocked=False,
                ),
                ReplayPointModel(
                    feature_id="feat-order-imbalance",
                    timestamp=computed_at,
                    expected_value=100000.0,
                    actual_value=100120.0,
                    trust_score=100.0,
                    blocked=False,
                ),
            ],
        )

    monkeypatch.setattr(
        "app.services.live_vendor.BinanceSpotConnector.fetch_snapshot",
        _fake_fetch_snapshot,
    )

    with TestClient(app) as test_client:
        yield test_client


def test_metrics_overview_endpoint_returns_seeded_database_payload(client: TestClient):
    response = client.get("/api/v1/metrics/overview")

    assert response.status_code == 200
    body = response.json()

    assert len(body["metrics"]) == 4
    assert body["feeds_by_status"]["critical"] == 1
    assert body["metrics"][0]["value"] == "18"


def test_metrics_overview_vercel_service_path_alias_returns_same_payload(client: TestClient):
    response = client.get("/v1/metrics/overview")

    assert response.status_code == 200
    body = response.json()

    assert len(body["metrics"]) == 4
    assert body["feeds_by_status"]["critical"] == 1


def test_incident_acknowledgement_persists_and_updates_workflow(client: TestClient):
    acknowledge_response = client.post(
        "/api/v1/incidents/inc-1043/acknowledge",
        json={"acknowledged": True},
    )

    assert acknowledge_response.status_code == 200
    assert acknowledge_response.json()["acknowledged"] is True
    assert acknowledge_response.json()["status"] == "investigating"

    incidents_response = client.get("/api/v1/incidents")
    assert incidents_response.status_code == 200

    incident = next(
        item
        for item in incidents_response.json()
        if item["id"] == "inc-1043"
    )
    assert incident["acknowledged"] is True
    assert incident["status"] == "investigating"


def test_replay_endpoint_returns_persisted_history(client: TestClient):
    response = client.get("/api/v1/replay/feat-news-sentiment")

    assert response.status_code == 200
    body = response.json()

    assert body["feature_id"] == "feat-news-sentiment"
    assert len(body["points"]) == 10
    assert body["points"][-1]["blocked"] is False


def test_ingestion_runs_are_durably_recorded(client: TestClient):
    response = client.post("/api/v1/ingestion-runs")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "queued"
    assert body["run_id"]


def test_live_feed_health_refreshes_from_vendor_snapshot(live_client: TestClient):
    response = live_client.get("/api/v1/feeds/feed-binance-agg/health")

    assert response.status_code == 200
    body = response.json()

    assert body["schema_version"] == "binance-spot-v3"
    assert body["latest_snapshot"]["freshness"] == 88.89
    assert body["latest_snapshot"]["status"] == "healthy"
    assert body["latency_seconds"] == 2


def test_live_feature_and_ingestion_run_use_vendor_refresh(live_client: TestClient):
    feature_response = live_client.get("/api/v1/features/feat-order-imbalance/reliability")

    assert feature_response.status_code == 200
    feature_body = feature_response.json()
    assert feature_body["latest_value"] == 0.5
    assert feature_body["lineage"][0] == "binance:BTCUSDT"

    run_response = live_client.post("/api/v1/ingestion-runs")
    assert run_response.status_code == 200
    run_body = run_response.json()
    assert run_body["status"] == "completed"
    assert run_body["run_id"]


def test_live_mode_lists_only_live_backed_feeds(live_client: TestClient):
    response = live_client.get("/api/v1/feeds")
    assert response.status_code == 200
    body = response.json()
    assert sorted(feed["id"] for feed in body) == sorted([
        "feed-binance-agg",
        "feed-public-news",
        "feed-economic-calendar",
    ])


def test_live_mode_hides_seeded_demo_incidents(live_client: TestClient):
    response = live_client.get("/api/v1/incidents")
    assert response.status_code == 200
    body = response.json()
    expected_live_feed_ids = {
        "feed-binance-agg",
        "feed-public-news",
        "feed-economic-calendar",
    }
    assert len(body) > 0
    assert all(item["id"] not in {"inc-1042", "inc-1043"} for item in body)
    assert all(item["feed_id"] in expected_live_feed_ids for item in body)
