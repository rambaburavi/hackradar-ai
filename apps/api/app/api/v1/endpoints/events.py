from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from app.api.dependencies import (
    DatabaseSession,
    require_dev_access,
)

from app.schemas.common import PaginatedResponse

from app.schemas.event import (
    EventCreate,
    EventFilters,
    EventRead,
)

from app.schemas.provenance import (
    EventDetailRead,
    VerificationLogRead,
)

from app.services.event import EventService
from app.services.event_detail import EventDetailService


router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


@router.get(
    "",
    response_model=PaginatedResponse[EventRead],
)
def list_events(
    db: DatabaseSession,
    filters: Annotated[EventFilters, Query()],
):
    return EventService(db).list_events(filters)


@router.get(
    "/upcoming",
    response_model=list[EventRead],
)
def upcoming_events(
    db: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return EventService(db).get_upcoming(limit)


@router.get(
    "/deadlines",
    response_model=list[EventRead],
)
def event_deadlines(
    db: DatabaseSession,
    days: Annotated[int, Query(ge=1, le=365)] = 7,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return EventService(db).get_deadlines(
        days=days,
        limit=limit,
    )


@router.get(
    "/{event_id}",
    response_model=EventDetailRead,
)
def get_event(
    event_id: UUID,
    db: DatabaseSession,
):
    result = EventDetailService(
        db
    ).get_event_detail(event_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return result


@router.get(
    "/{event_id}/verification",
    response_model=list[VerificationLogRead],
)
def get_verification_history(
    event_id: UUID,
    db: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    result = EventDetailService(
        db
    ).get_verification_history(
        event_id,
        limit,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    return result


@router.post(
    "",
    response_model=EventRead,
    status_code=201,
    dependencies=[Depends(require_dev_access)],
)
def create_event(
    payload: EventCreate,
    db: DatabaseSession,
):
    return EventService(db).create_event(payload)