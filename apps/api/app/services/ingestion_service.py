from __future__ import annotations

from ..repositories import IngestionRepository


class IngestionService:
    def __init__(self, session):
        self.repository = IngestionRepository(session)

    def create_ingestion_run(self) -> dict[str, str]:
        run = self.repository.create_run()
        return {
            "status": run.status,
            "message": "Database-backed ingestion scheduled",
            "run_id": run.id,
        }
