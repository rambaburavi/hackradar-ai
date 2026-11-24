from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import DatabaseSession

from app.core.enums import DiscoveryRunStatus

from app.repositories.discovery_run import (
    DiscoveryRunRepository,
)

from app.schemas.common import PaginatedResponse

from app.schemas.discovery import DiscoveryRunRead


router = APIRouter(
    prefix="/discovery",
    tags=["Discovery Runs"],
)


@router.get(
    "/runs",
    response_model=PaginatedResponse[DiscoveryRunRead],
)
def list_discovery_runs(
    db: DatabaseSession,
    source_id: UUID | None = None,
    status: DiscoveryRunStatus | None = None,
    page: Annotated[int, Query(ge=1, le=10000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    runs, total = DiscoveryRunRepository(
        db
    ).list_runs(
        source_id=source_id,
        status=status,
        page=page,
        page_size=page_size,
    )

    total_pages = ceil(total / page_size)

    return PaginatedResponse[DiscoveryRunRead](
        items=[
            DiscoveryRunRead.model_validate(run)
            for run in runs
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=total_pages > 0 and page > 1,
    )


@router.get(
    "/runs/{run_id}",
    response_model=DiscoveryRunRead,
)
def get_discovery_run(
    run_id: UUID,
    db: DatabaseSession,
):
    run = DiscoveryRunRepository(db).get_by_id(
        run_id
    )

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Discovery run not found",
        )

    return run