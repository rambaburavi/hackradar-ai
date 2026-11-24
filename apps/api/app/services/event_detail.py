from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    EventSource,
    EligibilityCriteria,
    VerificationLog,
)

from app.repositories.event import EventRepository

from app.schemas.event import EventRead

from app.schemas.provenance import (
    EventDetailRead,
    EventSourceRead,
    EligibilityRead,
    VerificationLogRead,
)


class EventDetailService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = EventRepository(db)

    def get_event_detail(
        self,
        event_id: UUID,
    ) -> EventDetailRead | None:

        event = self.repository.get_by_id(event_id)

        if event is None:
            return None

        sources = self.db.scalars(
            select(EventSource)
            .where(EventSource.event_id == event_id)
            .order_by(
                EventSource.first_discovered_at.asc()
            )
        ).all()

        eligibility = self.db.scalar(
            select(EligibilityCriteria)
            .where(
                EligibilityCriteria.event_id == event_id
            )
        )

        event_data = EventRead.model_validate(
            event
        ).model_dump()

        return EventDetailRead(
            **event_data,
            sources=[
                EventSourceRead.model_validate(source)
                for source in sources
            ],
            eligibility=(
                EligibilityRead.model_validate(eligibility)
                if eligibility is not None
                else None
            ),
        )

    def get_verification_history(
        self,
        event_id: UUID,
        limit: int = 50,
    ) -> list[VerificationLogRead] | None:

        if self.repository.get_by_id(event_id) is None:
            return None

        statement = (
            select(VerificationLog)
            .where(
                VerificationLog.event_id == event_id
            )
            .order_by(
                VerificationLog.verified_at.desc(),
                VerificationLog.id.asc(),
            )
            .limit(limit)
        )

        return [
            VerificationLogRead.model_validate(log)
            for log in self.db.scalars(statement).all()
        ]