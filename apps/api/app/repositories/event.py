from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    DiscoverySource,
    Event,
    EventSource,
)

from app.core.enums import EventLifecycleStatus

from app.schemas.event import EventFilters

from app.utils.normalization import normalize_title


class EventRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, event_id: UUID) -> Event | None:
        statement = (
            select(Event)
            .options(selectinload(Event.tags))
            .where(Event.id == event_id)
        )

        return self.db.scalar(statement)

    def get_by_slug(self, slug: str) -> Event | None:
        statement = (
            select(Event)
            .options(selectinload(Event.tags))
            .where(Event.slug == slug)
        )

        return self.db.scalar(statement)

    def create(self, event: Event) -> Event:
        self.db.add(event)
        self.db.flush()

        return event

    def update(self, event: Event) -> Event:
        self.db.flush()

        return event

    def delete(self, event: Event) -> None:
        self.db.delete(event)
        self.db.flush()

    def list_events(
        self,
        filters: EventFilters,
    ) -> tuple[list[Event], int]:

        conditions = []

        if filters.search and filters.search.strip():
            search = normalize_title(filters.search)

            conditions.append(
                or_(
                    Event.normalized_title.contains(
                        search,
                        autoescape=True,
                    ),
                    func.lower(Event.organizer).contains(
                        search,
                        autoescape=True,
                    ),
                    func.lower(Event.description).contains(
                        search,
                        autoescape=True,
                    ),
                )
            )

        if filters.category is not None:
            conditions.append(
                Event.category == filters.category
            )

        if filters.mode is not None:
            conditions.append(
                Event.mode == filters.mode
            )

        if filters.country:
            conditions.append(
                func.lower(Event.country)
                == filters.country.strip().lower()
            )

        if filters.state:
            conditions.append(
                func.lower(Event.state)
                == filters.state.strip().lower()
            )

        if filters.city:
            conditions.append(
                func.lower(Event.city)
                == filters.city.strip().lower()
            )

        if filters.lifecycle_status is not None:
            conditions.append(
                Event.lifecycle_status
                == filters.lifecycle_status
            )

        if filters.verification_status is not None:
            conditions.append(
                Event.verification_status
                == filters.verification_status
            )

        if filters.source:
            source_query = (
                select(EventSource.event_id)
                .join(
                    DiscoverySource,
                    EventSource.discovery_source_id
                    == DiscoverySource.id,
                )
                .where(
                    DiscoverySource.source_identifier
                    == filters.source.strip().lower()
                )
            )

            conditions.append(
                Event.id.in_(source_query)
            )

        if filters.fee_type == "free":
            conditions.append(
                Event.registration_fee == 0
            )

        elif filters.fee_type == "paid":
            conditions.append(
                Event.registration_fee > 0
            )

        elif filters.fee_type == "unknown":
            conditions.append(
                Event.registration_fee.is_(None)
            )

        if filters.deadline_within_days is not None:
            now = datetime.now(timezone.utc)

            cutoff = now + timedelta(
                days=filters.deadline_within_days
            )

            conditions.extend([
                Event.registration_deadline >= now,
                Event.registration_deadline <= cutoff,
                Event.lifecycle_status.notin_([
                    EventLifecycleStatus.CANCELLED,
                    EventLifecycleStatus.COMPLETED,
                    EventLifecycleStatus.REGISTRATION_CLOSED,
                    EventLifecycleStatus.ONGOING,
                ]),
            ])

        count_statement = (
            select(func.count())
            .select_from(Event)
            .where(*conditions)
        )

        total = self.db.scalar(count_statement) or 0

        statement = (
            select(Event)
            .options(selectinload(Event.tags))
            .where(*conditions)
        )

        sort_options = {
            "newest": Event.created_at.desc(),
            "oldest": Event.created_at.asc(),
            "deadline": (
                Event.registration_deadline
                .asc()
                .nulls_last()
            ),
            "start_date": (
                Event.starts_at.asc().nulls_last()
            ),
            "title": Event.normalized_title.asc(),
        }

        statement = statement.order_by(
            sort_options[filters.sort_by],
            Event.id.asc(),
        )

        offset = (
            filters.page - 1
        ) * filters.page_size

        statement = (
            statement
            .offset(offset)
            .limit(filters.page_size)
        )

        events = list(
            self.db.scalars(statement).all()
        )

        return events, total

    def get_upcoming(
        self,
        limit: int = 20,
    ) -> list[Event]:

        now = datetime.now(timezone.utc)

        statement = (
            select(Event)
            .options(selectinload(Event.tags))
            .where(
                Event.starts_at >= now,
                Event.lifecycle_status.notin_([
                    EventLifecycleStatus.CANCELLED,
                    EventLifecycleStatus.COMPLETED,
                    EventLifecycleStatus.ONGOING,
                ]),
            )
            .order_by(
                Event.starts_at.asc(),
                Event.id.asc(),
            )
            .limit(max(1, min(limit, 100)))
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_deadlines(
        self,
        days: int = 7,
        limit: int = 100,
    ) -> list[Event]:

        now = datetime.now(timezone.utc)

        cutoff = now + timedelta(
            days=max(1, min(days, 365))
        )

        statement = (
            select(Event)
            .options(selectinload(Event.tags))
            .where(
                Event.registration_deadline >= now,
                Event.registration_deadline <= cutoff,
                Event.lifecycle_status.notin_([
                    EventLifecycleStatus.CANCELLED,
                    EventLifecycleStatus.COMPLETED,
                    EventLifecycleStatus.REGISTRATION_CLOSED,
                    EventLifecycleStatus.ONGOING,
                ]),
            )
            .order_by(
                Event.registration_deadline.asc(),
                Event.id.asc(),
            )
            .limit(max(1, min(limit, 100)))
        )

        return list(
            self.db.scalars(statement).all()
        )