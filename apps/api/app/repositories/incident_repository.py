from __future__ import annotations

from datetime import datetime
import json

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..models import IncidentEventModel, IncidentModel


class IncidentRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_incidents(self) -> list[IncidentModel]:
        statement = select(IncidentModel).order_by(desc(IncidentModel.started_at))
        return list(self.session.scalars(statement))

    def acknowledge(self, incident_id: str) -> IncidentModel:
        incident = self.session.get(IncidentModel, incident_id)
        incident.acknowledged = True
        if incident.status == "triage":
            incident.status = "investigating"
        self.session.add(
            IncidentEventModel(
                incident_id=incident_id,
                event_type="acknowledged",
                actor="operator-ui",
                payload_json=json.dumps({"acknowledged": True}),
                created_at=datetime.utcnow().replace(microsecond=0),
            )
        )
        self.session.commit()
        self.session.refresh(incident)
        return incident
