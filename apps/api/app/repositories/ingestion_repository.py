from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from ..models import IngestionRunModel


class IngestionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_run(self) -> IngestionRunModel:
        run = IngestionRunModel(
            id=f"run-{uuid4().hex[:12]}",
            feed_id="seeded-system",
            run_type="seeded",
            status="queued",
            started_at=datetime.utcnow().replace(microsecond=0),
            completed_at=None,
            record_count=0,
            error_summary=None,
        )
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run
