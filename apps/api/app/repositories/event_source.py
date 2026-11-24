from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EventSource


class EventSourceRepository:

    def __init__(self, db: Session):

        self.db = db

    def find_by_external_id(
        self,
        source_id: UUID,
        external_id: str,
    ) -> EventSource | None:

        statement = select(EventSource).where(
            EventSource.discovery_source_id == source_id,
            EventSource.external_id == external_id,
        )

        return self.db.scalar(statement)

    def find_by_url(
        self,
        source_id: UUID,
        canonical_url: str,
    ) -> EventSource | None:

        statement = select(EventSource).where(
            EventSource.discovery_source_id == source_id,
            EventSource.canonical_url == canonical_url,
        )

        return self.db.scalar(statement)

    def create(
        self,
        source: EventSource,
    ) -> EventSource:

        self.db.add(source)

        self.db.flush()

        return source