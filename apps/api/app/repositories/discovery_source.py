from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DiscoverySource


class DiscoverySourceRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        source_id: UUID,
    ) -> DiscoverySource | None:

        return self.db.get(
            DiscoverySource,
            source_id,
        )

    def get_by_identifier(
        self,
        identifier: str,
    ) -> DiscoverySource | None:

        statement = select(DiscoverySource).where(
            DiscoverySource.source_identifier
            == identifier.strip().lower()
        )

        return self.db.scalar(statement)

    def list_sources(
        self,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DiscoverySource]:

        statement = select(DiscoverySource)

        if enabled_only:
            statement = statement.where(
                DiscoverySource.enabled.is_(True)
            )

        statement = (
            statement
            .order_by(DiscoverySource.name.asc())
            .offset(max(0, offset))
            .limit(max(1, min(limit, 100)))
        )

        return list(
            self.db.scalars(statement).all()
        )

    def create(
        self,
        source: DiscoverySource,
    ) -> DiscoverySource:

        self.db.add(source)
        self.db.flush()

        return source