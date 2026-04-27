from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from ..models import IngestionRunModel


class IngestionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_run(
        self,
        feed_id: str = "seeded-system",
        run_type: str = "seeded",
        status: str = "queued",
    ) -> IngestionRunModel:
        run = IngestionRunModel(
            id=f"run-{uuid4().hex[:12]}",
            feed_id=feed_id,
            run_type=run_type,
            status=status,
            started_at=datetime.utcnow().replace(microsecond=0),
            completed_at=None,
            record_count=0,
            error_summary=None,
        )
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def mark_completed(self, run_id: str, record_count: int) -> IngestionRunModel:
        run = self.session.get(IngestionRunModel, run_id)
        run.status = "completed"
        run.completed_at = datetime.utcnow().replace(microsecond=0)
        run.record_count = record_count
        run.error_summary = None
        self.session.commit()
        self.session.refresh(run)
        return run

    def mark_failed(self, run_id: str, error_summary: str) -> IngestionRunModel:
        run = self.session.get(IngestionRunModel, run_id)
        run.status = "failed"
        run.completed_at = datetime.utcnow().replace(microsecond=0)
        run.error_summary = error_summary
        self.session.commit()
        self.session.refresh(run)
        return run
