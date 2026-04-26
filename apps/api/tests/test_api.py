from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_overview_endpoint_returns_seeded_dashboard_payload():
    response = client.get("/api/v1/metrics/overview")
    assert response.status_code == 200
    body = response.json()
    assert len(body["metrics"]) == 4
    assert body["feeds_by_status"]["critical"] == 1


def test_incident_acknowledgement_sets_flag():
    response = client.post("/api/v1/incidents/inc-1043/acknowledge", json={"acknowledged": True})
    assert response.status_code == 200
    assert response.json()["acknowledged"] is True
