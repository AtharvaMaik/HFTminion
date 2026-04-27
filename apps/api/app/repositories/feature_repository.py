from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..models import FeatureModel, FeatureSnapshotModel


class FeatureRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_features(self) -> list[FeatureModel]:
        return list(self.session.scalars(select(FeatureModel).order_by(FeatureModel.name)))

    def get_feature(self, feature_id: str) -> FeatureModel:
        return self.session.get(FeatureModel, feature_id)

    def get_latest_snapshot(self, feature_id: str) -> FeatureSnapshotModel:
        statement = (
            select(FeatureSnapshotModel)
            .where(FeatureSnapshotModel.feature_id == feature_id)
            .order_by(desc(FeatureSnapshotModel.source_timestamp), desc(FeatureSnapshotModel.id))
            .limit(1)
        )
        return self.session.scalars(statement).one()

    def create_snapshot(self, snapshot: FeatureSnapshotModel) -> FeatureSnapshotModel:
        self.session.add(snapshot)
        self.session.flush()
        return snapshot
