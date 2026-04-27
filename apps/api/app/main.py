from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

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
from .config import get_settings
from .db import get_db_session, get_engine, get_session_factory
from .schemas import AcknowledgeIncidentRequest, IncidentRecord
from .seed import initialize_database, seed_database
from .services import CurrentStateService, IngestionService, IncidentService


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.data_mode == "database":
        engine = get_engine()
        initialize_database(engine)
        with get_session_factory()() as session:
            seed_database(session)
    yield


app = FastAPI(title="AltData Reliability OS API", version="0.1.0", lifespan=lifespan)


def _is_database_mode() -> bool:
    return get_settings().data_mode == "database"


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/feeds")
@app.get("/api/v1/feeds")
def get_feeds(session: Session = Depends(get_db_session)):
    if _is_database_mode():
        return CurrentStateService(session).list_feeds()
    return list_feeds()


@app.get("/v1/feeds/{feed_id}/health")
@app.get("/api/v1/feeds/{feed_id}/health")
def get_feed_detail(feed_id: str, session: Session = Depends(get_db_session)):
    if _is_database_mode():
        return CurrentStateService(session).get_feed_health(feed_id)
    return get_feed_health(feed_id)


@app.post("/v1/ingestion-runs")
@app.post("/api/v1/ingestion-runs")
def create_ingestion_run(session: Session = Depends(get_db_session)) -> dict[str, str]:
    if _is_database_mode():
        return IngestionService(session).create_ingestion_run()
    return {"status": "queued", "message": "Synthetic ingestion scheduled"}


@app.get("/v1/features")
@app.get("/api/v1/features")
def get_features(session: Session = Depends(get_db_session)):
    if _is_database_mode():
        return CurrentStateService(session).list_features()
    return list_features()


@app.get("/v1/features/{feature_id}/reliability")
@app.get("/api/v1/features/{feature_id}/reliability")
def get_feature_reliability(feature_id: str, session: Session = Depends(get_db_session)):
    if _is_database_mode():
        return CurrentStateService(session).get_feature_snapshot(feature_id)
    return get_feature_snapshot(feature_id)


@app.get("/v1/incidents")
@app.get("/api/v1/incidents")
def get_incidents(session: Session = Depends(get_db_session)):
    if _is_database_mode():
        return CurrentStateService(session).list_incidents()
    return list_incidents()


@app.post("/v1/incidents/{incident_id}/acknowledge", response_model=IncidentRecord)
@app.post("/api/v1/incidents/{incident_id}/acknowledge", response_model=IncidentRecord)
def post_acknowledge_incident(
    incident_id: str,
    _: AcknowledgeIncidentRequest,
    session: Session = Depends(get_db_session),
):
    if _is_database_mode():
        return IncidentService(session).acknowledge_incident(incident_id)
    return acknowledge_incident(incident_id)


@app.get("/v1/metrics/overview")
@app.get("/api/v1/metrics/overview")
def get_metrics_overview(session: Session = Depends(get_db_session)):
    if _is_database_mode():
        return CurrentStateService(session).metrics_overview()
    return metrics_overview()


@app.get("/v1/replay/{feature_id}")
@app.get("/api/v1/replay/{feature_id}")
def get_replay(feature_id: str, session: Session = Depends(get_db_session)):
    if _is_database_mode():
        return CurrentStateService(session).replay(feature_id)
    return replay(feature_id)

