from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Event

from app.repositories.event import EventRepository

from app.schemas.common import PaginatedResponse

from app.schemas.event import (
    EventCreate,
    EventFilters,
    EventRead,
)

from app.utils.normalization import (
    generate_slug,
    normalize_title,
)


class EventService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = EventRepository(db)

    def create_event(
        self,
        payload: EventCreate,
    ) -> EventRead:

        values = payload.model_dump()

        for field in (
            "official_url",
            "registration_url",
        ):
            if values[field] is not None:
                values[field] = str(values[field])

        event = Event(
            **values,
            normalized_title=normalize_title(
                payload.title
            ),
            slug=generate_slug(payload.title),
        )

        try:
            self.repository.create(event)

            self.db.refresh(event)

            response = EventRead.model_validate(event)

            self.db.commit()

            return response

        except Exception:
            self.db.rollback()
            raise

    def get_event(
        self,
        event_id: UUID,
    ) -> EventRead | None:

        event = self.repository.get_by_id(
            event_id
        )

        if event is None:
            return None

        return EventRead.model_validate(event)

    def list_events(
        self,
        filters: EventFilters,
    ) -> PaginatedResponse[EventRead]:

        events, total = (
            self.repository.list_events(filters)
        )

        total_pages = ceil(
            total / filters.page_size
        )

        return PaginatedResponse[EventRead](
            items=[
                EventRead.model_validate(event)
                for event in events
            ],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
            has_next=filters.page < total_pages,
            has_previous=(
                total_pages > 0
                and filters.page > 1
            ),
        )

    def get_upcoming(
        self,
        limit: int = 20,
    ) -> list[EventRead]:

        return [
            EventRead.model_validate(event)
            for event in
            self.repository.get_upcoming(limit)
        ]

    def get_deadlines(
        self,
        days: int = 7,
        limit: int = 100,
    ) -> list[EventRead]:

        return [
            EventRead.model_validate(event)
            for event in
            self.repository.get_deadlines(
                days,
                limit,
            )
        ]