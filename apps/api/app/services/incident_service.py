from __future__ import annotations

from ..repositories import IncidentRepository
from ..schemas import IncidentRecord
from .current_state import _serialize_incident


class IncidentService:
    def __init__(self, session):
        self.repository = IncidentRepository(session)

    def acknowledge_incident(self, incident_id: str) -> IncidentRecord:
        return _serialize_incident(self.repository.acknowledge(incident_id))
