from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import DiscoveryRunStatus
from app.models import DiscoveryRun


class DiscoveryRunRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        run_id: UUID,
    ) -> DiscoveryRun | None:

        return self.db.get(
            DiscoveryRun,
            run_id,
        )

    def create(
        self,
        run: DiscoveryRun,
    ) -> DiscoveryRun:

        self.db.add(run)
        self.db.flush()

        return run

    def list_runs(
        self,
        source_id: UUID | None = None,
        status: DiscoveryRunStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DiscoveryRun], int]:

        conditions = []

        if source_id is not None:
            conditions.append(
                DiscoveryRun.source_id == source_id
            )

        if status is not None:
            conditions.append(
                DiscoveryRun.status == status
            )

        page = max(1, min(page, 10000))

        page_size = max(
            1,
            min(page_size, 100),
        )

        total = self.db.scalar(
            select(func.count())
            .select_from(DiscoveryRun)
            .where(*conditions)
        ) or 0

        statement = (
            select(DiscoveryRun)
            .where(*conditions)
            .order_by(
                DiscoveryRun.created_at.desc(),
                DiscoveryRun.id.asc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return (
            list(self.db.scalars(statement).all()),
            total,
        )

    def get_latest(
        self,
        source_id: UUID | None = None,
    ) -> DiscoveryRun | None:

        statement = select(DiscoveryRun)

        if source_id is not None:
            statement = statement.where(
                DiscoveryRun.source_id == source_id
            )

        statement = (
            statement
            .order_by(
                DiscoveryRun.created_at.desc(),
                DiscoveryRun.id.asc(),
            )
            .limit(1)
        )

        return self.db.scalar(statement)