from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test-altdata.db"
    monkeypatch.setenv("DATA_MODE", "database")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    with TestClient(app) as test_client:
        yield test_client


def test_metrics_overview_endpoint_returns_seeded_database_payload(client: TestClient):
    response = client.get("/api/v1/metrics/overview")

    assert response.status_code == 200
    body = response.json()

    assert len(body["metrics"]) == 4
    assert body["feeds_by_status"]["critical"] == 1
    assert body["metrics"][0]["value"] == "18"


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
