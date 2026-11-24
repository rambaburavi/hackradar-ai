from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import DatabaseSession

from app.repositories.discovery_source import (
    DiscoverySourceRepository,
)

from app.schemas.discovery import DiscoverySourceRead


router = APIRouter(
    prefix="/sources",
    tags=["Discovery Sources"],
)


@router.get(
    "",
    response_model=list[DiscoverySourceRead],
)
def list_sources(
    db: DatabaseSession,
    enabled_only: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
):
    return DiscoverySourceRepository(
        db
    ).list_sources(
        enabled_only=enabled_only,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{identifier}",
    response_model=DiscoverySourceRead,
)
def get_source(
    identifier: str,
    db: DatabaseSession,
):
    source = DiscoverySourceRepository(
        db
    ).get_by_identifier(identifier)

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Discovery source not found",
        )

    return source