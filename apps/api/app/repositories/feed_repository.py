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

    def get_latest_snapshot_or_none(self, feed_id: str) -> FeedSnapshotModel | None:
        statement = (
            select(FeedSnapshotModel)
            .where(FeedSnapshotModel.feed_id == feed_id)
            .order_by(desc(FeedSnapshotModel.computed_at), desc(FeedSnapshotModel.id))
            .limit(1)
        )
        return self.session.scalars(statement).first()

    def get_latest_snapshot(self, feed_id: str) -> FeedSnapshotModel:
        return self.get_latest_snapshot_or_none(feed_id)

    def create_snapshot(self, snapshot: FeedSnapshotModel) -> FeedSnapshotModel:
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def update_status(self, feed_id: str, status: str) -> None:
        feed = self.get_feed(feed_id)
        feed.status = status
        self.session.add(feed)
