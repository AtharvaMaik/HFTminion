from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ReplayPointModel


class ReplayRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_points(self, feature_id: str) -> list[ReplayPointModel]:
        statement = (
            select(ReplayPointModel)
            .where(ReplayPointModel.feature_id == feature_id)
            .order_by(ReplayPointModel.timestamp)
        )
        return list(self.session.scalars(statement))
