from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db


DatabaseSession = Annotated[Session, Depends(get_db)]


def require_dev_access(
    api_key: Annotated[
        str | None,
        Header(alias="X-Dev-API-Key"),
    ] = None,
) -> None:

    if not settings.ENABLE_DEV_MUTATIONS:
        raise HTTPException(
            status_code=404,
            detail="Not found",
        )

    expected_key = settings.DEV_API_KEY

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="Development access is not configured",
        )

    if not api_key or not compare_digest(
        api_key.encode("utf-8"),
        expected_key.encode("utf-8"),
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )