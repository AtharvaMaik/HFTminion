from __future__ import annotations

from fastapi import FastAPI

from .data import (
    acknowledge_incident,
    get_feature_snapshot,
    get_feed_health,
    list_features,
    list_feeds,
    list_incidents,
    metrics_overview,
    replay,
)
from .schemas import AcknowledgeIncidentRequest, IncidentRecord

app = FastAPI(title="AltData Reliability OS API", version="0.1.0")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/feeds")
def get_feeds():
    return list_feeds()


@app.get("/api/v1/feeds/{feed_id}/health")
def get_feed_detail(feed_id: str):
    return get_feed_health(feed_id)


@app.post("/api/v1/ingestion-runs")
def create_ingestion_run() -> dict[str, str]:
    return {"status": "queued", "message": "Synthetic ingestion scheduled"}


@app.get("/api/v1/features")
def get_features():
    return list_features()


@app.get("/api/v1/features/{feature_id}/reliability")
def get_feature_reliability(feature_id: str):
    return get_feature_snapshot(feature_id)


@app.get("/api/v1/incidents")
def get_incidents():
    return list_incidents()


@app.post("/api/v1/incidents/{incident_id}/acknowledge", response_model=IncidentRecord)
def post_acknowledge_incident(incident_id: str, _: AcknowledgeIncidentRequest):
    return acknowledge_incident(incident_id)


@app.get("/api/v1/metrics/overview")
def get_metrics_overview():
    return metrics_overview()


@app.get("/api/v1/replay/{feature_id}")
def get_replay(feature_id: str):
    return replay(feature_id)

