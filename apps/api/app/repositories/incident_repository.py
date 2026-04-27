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

    def get_incident(self, incident_id: str) -> IncidentModel | None:
        return self.session.get(IncidentModel, incident_id)

    def upsert_live_incident(
        self,
        incident_id: str,
        *,
        feed_id: str,
        title: str,
        severity: str,
        status: str,
        summary: str,
        impacted_features: list[str],
    ) -> IncidentModel:
        incident = self.get_incident(incident_id)
        event_type = "opened"
        now = datetime.utcnow().replace(microsecond=0)
        if incident is None:
            incident = IncidentModel(
                id=incident_id,
                title=title,
                feed_id=feed_id,
                severity=severity,
                status=status,
                started_at=now,
                acknowledged=False,
                summary=summary,
                impacted_features=json.dumps(impacted_features),
            )
            self.session.add(incident)
        else:
            event_type = "reclassified"
            incident.title = title
            incident.severity = severity
            incident.status = status
            incident.summary = summary
            incident.impacted_features = json.dumps(impacted_features)
            self.session.add(incident)

        self.session.add(
            IncidentEventModel(
                incident_id=incident_id,
                event_type=event_type,
                actor="live-vendor-engine",
                payload_json=json.dumps(
                    {
                        "severity": severity,
                        "status": status,
                        "summary": summary,
                    }
                ),
                created_at=now,
            )
        )
        self.session.commit()
        self.session.refresh(incident)
        return incident

    def resolve_live_incident(self, incident_id: str) -> None:
        incident = self.get_incident(incident_id)
        if incident is None or incident.status == "resolved":
            return

        incident.status = "resolved"
        self.session.add(incident)
        self.session.add(
            IncidentEventModel(
                incident_id=incident_id,
                event_type="resolved",
                actor="live-vendor-engine",
                payload_json=json.dumps({"resolved": True}),
                created_at=datetime.utcnow().replace(microsecond=0),
            )
        )
        self.session.commit()
