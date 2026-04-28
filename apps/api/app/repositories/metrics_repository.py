from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..models import FeedModel, FeedSnapshotModel, FeatureSnapshotModel, IncidentModel


class MetricsRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_feeds(self) -> list[FeedModel]:
        return list(self.session.scalars(select(FeedModel)))

    def list_latest_snapshots(self) -> list[FeedSnapshotModel]:
        feeds = self.list_feeds()
        snapshots: list[FeedSnapshotModel] = []
        for feed in feeds:
            statement = (
                select(FeedSnapshotModel)
                .where(FeedSnapshotModel.feed_id == feed.id)
                .order_by(desc(FeedSnapshotModel.computed_at), desc(FeedSnapshotModel.id))
                .limit(1)
            )
            snapshot = self.session.scalars(statement).first()
            if snapshot is not None:
                snapshots.append(snapshot)
        return snapshots

    def list_incidents(self) -> list[IncidentModel]:
        return list(self.session.scalars(select(IncidentModel).order_by(desc(IncidentModel.started_at))))

    def count_blocked_features(self) -> int:
        statement = select(FeatureSnapshotModel).where(FeatureSnapshotModel.blocked.is_(True))
        return len(list(self.session.scalars(statement)))

    def list_recent_snapshots(
        self,
        since: datetime,
        feed_ids: list[str] | None = None,
    ) -> list[FeedSnapshotModel]:
        statement = select(FeedSnapshotModel).where(FeedSnapshotModel.computed_at >= since)
        if feed_ids:
            statement = statement.where(FeedSnapshotModel.feed_id.in_(feed_ids))
        statement = statement.order_by(FeedSnapshotModel.computed_at.asc(), FeedSnapshotModel.id.asc())
        return list(self.session.scalars(statement))
