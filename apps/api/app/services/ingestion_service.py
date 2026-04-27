from __future__ import annotations

from .live_vendor import LiveFeedRefreshService
from ..repositories import IngestionRepository


class IngestionService:
    def __init__(self, session):
        self.session = session
        self.repository = IngestionRepository(session)
        self.live_refresh = LiveFeedRefreshService(session)

    def create_ingestion_run(self) -> dict[str, str]:
        if self.live_refresh.is_live_mode_enabled():
            run = self.live_refresh.refresh_live_feed()
            return {
                "status": run.status,
                "message": "Live vendor ingestion completed",
                "run_id": run.id,
            }

        run = self.repository.create_run()
        return {
            "status": run.status,
            "message": "Database-backed ingestion scheduled",
            "run_id": run.id,
        }
