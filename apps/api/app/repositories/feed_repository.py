from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..models import FeedModel, FeedSnapshotModel


class FeedRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_feeds(self) -> list[FeedModel]:
        return list(self.session.scalars(select(FeedModel).order_by(FeedModel.name)))

    def get_feed(self, feed_id: str) -> FeedModel:
        return self.session.get(FeedModel, feed_id)

    def get_latest_snapshot(self, feed_id: str) -> FeedSnapshotModel:
        statement = (
            select(FeedSnapshotModel)
            .where(FeedSnapshotModel.feed_id == feed_id)
            .order_by(desc(FeedSnapshotModel.computed_at))
            .limit(1)
        )
        return self.session.scalars(statement).one()
