from __future__ import annotations

from sqlalchemy import delete, select
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

    def replace_points(self, feature_id: str, points: list[ReplayPointModel]) -> None:
        self.session.execute(delete(ReplayPointModel).where(ReplayPointModel.feature_id == feature_id))
        self.session.add_all(points)
