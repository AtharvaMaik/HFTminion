from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import data as app_data
from app import seed as app_seed
from app.main import app
from app.models import ReplayPointModel
from app.schemas import FeedDefinition
from app.schemas import ReliabilitySnapshot
from app.services.live_connectors import LiveConnectorSnapshot
from app.services.live_registry import LIVE_FEATURE_IDS
from app.services.live_registry import LIVE_FEED_IDS
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
            id="feed-demo-legacy",
            name="DEMO_LEGACY_PLACEHOLDER",
            vendor="Demo Placeholder Source",
            region="us-west-2",
            feed_class="news_event_feed",
            freshness_sla_seconds=120,
            coverage_target_pct=88.0,
            status="warning",
        ),
    ]
    live_snapshots = {
        **app_data.SNAPSHOTS,
        "feed-demo-legacy": ReliabilitySnapshot(
            timestamp=live_timestamp,
            freshness=61.0,
            completeness=72.0,
            schema_stability=70.0,
            entity_coverage=68.0,
            revision_rate=64.0,
            drift_anomaly_score=66.0,
            weighted_trust_score=68.5,
            status="warning",
        ),
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

    def _fake_fetch_snapshot(self, freshness_sla_seconds: int) -> BinanceSnapshot:
        computed_at = datetime.utcnow().replace(microsecond=0)
        return BinanceSnapshot(
            symbol=self.default_symbol,
            source_name="Binance",
            source_lineage_prefix=[f"binance:{self.default_symbol}", "api/v3/depth", "api/v3/ticker/24hr"],
            primary_feature_id="feat-order-imbalance",
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

    def _fake_public_news_snapshot(self, freshness_sla_seconds: int) -> LiveConnectorSnapshot:
        computed_at = datetime.utcnow().replace(microsecond=0)
        return LiveConnectorSnapshot(
            symbol="public-news-rss",
            source_name="Public News RSS",
            source_lineage_prefix=["source:public-news-rss", "rss:item-count"],
            primary_feature_id="feat-headline-velocity",
            avg_price=24.0,
            last_price=7.0,
            price_change_pct=0.0,
            latency_seconds=18,
            schema_version="rss-2.0",
            bid_qty=7.0,
            ask_qty=17.0,
            trade_count=24,
            quote_volume=24.0,
            freshness_score=81.5,
            completeness_score=96.0,
            schema_stability_score=92.0,
            entity_coverage_score=88.0,
            revision_rate_score=76.0,
            drift_anomaly_score=90.0,
            feature_value=0.2917,
            computed_at=computed_at,
            replay_points=[
                ReplayPointModel(
                    feature_id="feat-headline-velocity",
                    timestamp=computed_at - timedelta(minutes=5),
                    expected_value=0.2917,
                    actual_value=0.25,
                    trust_score=87.0,
                    blocked=False,
                ),
                ReplayPointModel(
                    feature_id="feat-headline-velocity",
                    timestamp=computed_at,
                    expected_value=0.2917,
                    actual_value=0.2917,
                    trust_score=90.0,
                    blocked=False,
                ),
            ],
        )

    monkeypatch.setattr(
        "app.services.live_connectors.PublicNewsRssConnector.fetch_snapshot",
        _fake_public_news_snapshot,
    )

    def _fake_economic_calendar_snapshot(self, freshness_sla_seconds: int) -> LiveConnectorSnapshot:
        computed_at = datetime.utcnow().replace(microsecond=0)
        return LiveConnectorSnapshot(
            symbol="fed-press-releases",
            source_name="Federal Reserve Press Releases",
            source_lineage_prefix=["source:economic-calendar", "calendar:event-rate"],
            primary_feature_id="feat-economic-event-pressure",
            avg_price=12.0,
            last_price=4.0,
            price_change_pct=25.0,
            latency_seconds=20,
            schema_version="rss-2.0",
            bid_qty=4.0,
            ask_qty=2.0,
            trade_count=18,
            quote_volume=24.0,
            freshness_score=93.4,
            completeness_score=98.0,
            schema_stability_score=95.0,
            entity_coverage_score=84.0,
            revision_rate_score=63.0,
            drift_anomaly_score=91.0,
            feature_value=0.625,
            computed_at=computed_at,
            replay_points=[
                ReplayPointModel(
                    feature_id="feat-economic-event-pressure",
                    timestamp=computed_at - timedelta(hours=6),
                    expected_value=0.625,
                    actual_value=0.5,
                    trust_score=88.0,
                    blocked=False,
                ),
                ReplayPointModel(
                    feature_id="feat-economic-event-pressure",
                    timestamp=computed_at + timedelta(hours=2),
                    expected_value=0.625,
                    actual_value=0.75,
                    trust_score=91.0,
                    blocked=False,
                ),
            ],
        )

    monkeypatch.setattr(
        "app.services.live_connectors.FedEconomicCalendarConnector.fetch_snapshot",
        _fake_economic_calendar_snapshot,
    )

    live_incidents = [
        *app_data.INCIDENTS,
        app_data.IncidentRecord(
            id="inc-demo-legacy",
            title="Legacy demo feed still present",
            feed_id="feed-demo-legacy",
            severity="warning",
            status="triage",
            started_at=live_timestamp,
            acknowledged=False,
            summary="This demo incident should be filtered out in live mode later.",
            impacted_features=["Demo Legacy Placeholder"],
        ),
    ]
    monkeypatch.setattr(app_data, "INCIDENTS", live_incidents)
    monkeypatch.setattr(app_seed, "INCIDENTS", live_incidents)

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
        "/api/v1/incidents/inc-live-feed-public-news/acknowledge",
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
        if item["id"] == "inc-live-feed-public-news"
    )
    assert incident["acknowledged"] is True
    assert incident["status"] == "investigating"


def test_replay_endpoint_returns_persisted_history(client: TestClient):
    response = client.get("/api/v1/replay/feat-headline-velocity")

    assert response.status_code == 200
    body = response.json()

    assert body["feature_id"] == "feat-headline-velocity"
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


def test_binance_snapshot_exposes_optional_live_connector_scores():
    computed_at = datetime.utcnow().replace(microsecond=0)
    snapshot = BinanceSnapshot(
        symbol="BTCUSDT",
        source_name="Binance",
        source_lineage_prefix=["binance:BTCUSDT"],
        primary_feature_id="feat-order-imbalance",
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
        replay_points=[],
    )

    assert snapshot.freshness_score is None
    assert snapshot.completeness_score is None
    assert snapshot.schema_stability_score is None
    assert snapshot.entity_coverage_score is None
    assert snapshot.revision_rate_score is None
    assert snapshot.drift_anomaly_score is None
    assert snapshot.feature_value is None


def test_live_news_feed_health_uses_real_source_shape(live_client: TestClient):
    response = live_client.get("/api/v1/feeds/feed-public-news/health")
    assert response.status_code == 200
    body = response.json()
    assert body["feed"]["id"] == "feed-public-news"
    assert body["schema_version"].startswith("rss-")
    assert body["latest_snapshot"]["freshness"] == 81.5
    assert body["latest_snapshot"]["completeness"] == 96.0


def test_live_news_feed_uses_connector_supplied_reliability_scores(live_client: TestClient):
    response = live_client.get("/api/v1/feeds/feed-public-news/health")
    assert response.status_code == 200
    body = response.json()

    assert body["schema_version"] == "rss-2.0"
    assert body["latest_snapshot"]["freshness"] == 81.5
    assert body["latest_snapshot"]["completeness"] == 96.0
    assert body["latest_snapshot"]["schema_stability"] == 92.0
    assert body["latest_snapshot"]["entity_coverage"] == 88.0
    assert body["latest_snapshot"]["revision_rate"] == 76.0
    assert body["latest_snapshot"]["drift_anomaly_score"] == 90.0

    feature_response = live_client.get("/api/v1/features/feat-headline-velocity/reliability")
    assert feature_response.status_code == 200
    feature_body = feature_response.json()
    assert feature_body["latest_value"] == 0.2917
    assert feature_body["lineage"] == [
        "source:public-news-rss",
        "rss:item-count",
        "feat-headline-velocity",
    ]


def test_live_economic_calendar_feed_uses_connector_supplied_macro_shape(live_client: TestClient):
    response = live_client.get("/api/v1/feeds/feed-economic-calendar/health")
    assert response.status_code == 200
    body = response.json()

    assert body["feed"]["id"] == "feed-economic-calendar"
    assert body["schema_version"] == "rss-2.0"
    assert body["latest_snapshot"]["freshness"] == 93.4
    assert body["latest_snapshot"]["completeness"] == 98.0
    assert body["latest_snapshot"]["schema_stability"] == 95.0
    assert body["latest_snapshot"]["entity_coverage"] == 84.0
    assert body["latest_snapshot"]["revision_rate"] == 63.0
    assert body["latest_snapshot"]["drift_anomaly_score"] == 91.0

    feature_response = live_client.get("/api/v1/features/feat-economic-event-pressure/reliability")
    assert feature_response.status_code == 200
    feature_body = feature_response.json()
    assert feature_body["latest_value"] == 0.625
    assert feature_body["lineage"] == [
        "source:economic-calendar",
        "calendar:event-rate",
        "feat-economic-event-pressure",
    ]


def test_fed_economic_calendar_connector_parses_real_rss_shape(monkeypatch: pytest.MonkeyPatch):
    from app.services.live_connectors import FedEconomicCalendarConnector

    now = datetime.utcnow().replace(microsecond=0, second=0, minute=0)
    sample_feed = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<rss version="2.0">',
            "<channel>",
            "<title>Federal Reserve Press Releases</title>",
            f"<item><title>Employment Situation</title><pubDate>{(now - timedelta(days=3)).strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate></item>",
            f"<item><title>Consumer Price Index</title><pubDate>{(now - timedelta(days=1)).strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate></item>",
            f"<item><title>Producer Price Index</title><pubDate>{(now + timedelta(hours=12)).strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate></item>",
            f"<item><title>Employment Situation</title><pubDate>{(now + timedelta(days=8)).strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate></item>",
            "</channel>",
            "</rss>",
        ]
    )

    connector = FedEconomicCalendarConnector()
    monkeypatch.setattr(connector, "_get_feed_xml", lambda: sample_feed)

    snapshot = connector.fetch_snapshot(freshness_sla_seconds=300)

    assert snapshot.schema_version == "rss-2.0"
    assert snapshot.source_lineage_prefix == [
        "source:economic-calendar",
        "calendar:event-rate",
    ]
    assert 0.0 <= snapshot.freshness_score <= 100.0
    assert 0.0 <= snapshot.completeness_score <= 100.0
    assert snapshot.schema_stability_score is not None
    assert snapshot.schema_stability_score < 100.0
    assert snapshot.trade_count == 4
    assert snapshot.feature_value is not None
    assert snapshot.replay_points


def test_public_news_connector_treats_unparseable_dates_as_missing():
    from app.services.live_connectors import PublicNewsRssConnector

    connector = PublicNewsRssConnector()
    item = ET.fromstring(
        "<item><title>Example headline</title><pubDate>not-a-real-date</pubDate></item>"
    )

    title, published_at = connector._read_item(item)
    assert title == "Example headline"
    assert published_at is None


def test_public_news_connector_parses_rss_dates_without_commas():
    from app.services.live_connectors import PublicNewsRssConnector

    connector = PublicNewsRssConnector()
    item = ET.fromstring(
        "<item><title>Example headline</title><pubDate>27 Apr 2026 12:00:00 +0000</pubDate></item>"
    )

    _, published_at = connector._read_item(item)
    assert published_at is not None


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


def test_live_mode_feature_lineage_comes_from_connector(live_client: TestClient):
    response = live_client.get("/api/v1/features/feat-headline-velocity/reliability")
    assert response.status_code == 200
    body = response.json()
    assert body["lineage"][0].startswith("source:")


def test_live_mode_lists_only_live_backed_feeds(live_client: TestClient):
    response = live_client.get("/api/v1/feeds")
    assert response.status_code == 200
    body = response.json()
    assert sorted(feed["id"] for feed in body) == sorted(LIVE_FEED_IDS)


def test_live_mode_lists_only_live_backed_features(live_client: TestClient):
    response = live_client.get("/api/v1/features")
    assert response.status_code == 200
    body = response.json()
    assert sorted(feature["id"] for feature in body) == sorted(LIVE_FEATURE_IDS)


def test_live_mode_hides_seeded_demo_incidents(live_client: TestClient):
    response = live_client.get("/api/v1/incidents")
    assert response.status_code == 200
    body = response.json()
    assert len(body) > 0
    assert all(item["feed_id"] != "feed-demo-legacy" for item in body)
    assert all(item["feed_id"] in LIVE_FEED_IDS for item in body)


def test_live_mode_incidents_include_newly_opened_live_incidents_on_first_response(
    live_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    computed_at = datetime.utcnow().replace(microsecond=0)

    def _critical_binance_snapshot(self, freshness_sla_seconds: int) -> BinanceSnapshot:
        return BinanceSnapshot(
            symbol=self.default_symbol,
            source_name="Binance",
            source_lineage_prefix=[f"binance:{self.default_symbol}", "api/v3/depth", "api/v3/ticker/24hr"],
            primary_feature_id="feat-order-imbalance",
            avg_price=100000.0,
            last_price=100120.0,
            price_change_pct=18.0,
            latency_seconds=600,
            schema_version="binance-spot-v3",
            bid_qty=1.0,
            ask_qty=20.0,
            trade_count=2,
            quote_volume=1000.0,
            computed_at=computed_at,
            replay_points=[
                ReplayPointModel(
                    feature_id="feat-order-imbalance",
                    timestamp=computed_at,
                    expected_value=100000.0,
                    actual_value=100120.0,
                    trust_score=0.0,
                    blocked=True,
                ),
            ],
        )

    monkeypatch.setattr(
        "app.services.live_vendor.BinanceSpotConnector.fetch_snapshot",
        _critical_binance_snapshot,
    )

    response = live_client.get("/api/v1/incidents")
    assert response.status_code == 200
    body = response.json()

    assert any(item["id"] == "inc-live-feed-binance-agg" for item in body)


def test_live_mode_overview_counts_only_live_backed_records(live_client: TestClient):
    response = live_client.get("/api/v1/metrics/overview")
    assert response.status_code == 200
    body = response.json()

    metrics_by_label = {metric["label"]: metric for metric in body["metrics"]}

    assert metrics_by_label["Tracked feeds"]["value"] == "3"
    assert metrics_by_label["Active incidents"]["value"] == "0"
    assert metrics_by_label["Blocked features"]["value"] == "0"
    assert body["feeds_by_status"] == {
        "healthy": 3,
        "warning": 0,
        "critical": 0,
    }
    assert all(item["feed_id"] in LIVE_FEED_IDS for item in body["incidents"])


def test_live_registry_declares_all_live_feed_ids():
    assert LIVE_FEED_IDS == [
        "feed-binance-agg",
        "feed-public-news",
        "feed-economic-calendar",
    ]
