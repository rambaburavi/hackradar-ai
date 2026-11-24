from sqlalchemy.orm import Session

from app.discovery.registry import get_adapter
from app.models import DiscoverySource
from app.repositories.discovery_source import (
    DiscoverySourceRepository,
)


def register_source(
    db: Session,
    identifier: str,
    access_approved: bool = False,
    access_notes: str | None = None,
) -> DiscoverySource:

    identifier = identifier.strip().lower()

    adapter = get_adapter(identifier)

    repository = DiscoverySourceRepository(db)

    existing = repository.get_by_identifier(
        identifier
    )

    if existing is not None:

        if access_approved:
            existing.enabled = True

            existing.access_notes = (
                access_notes
                or "Access reviewed and approved."
            )

            db.flush()

        return existing

    source = DiscoverySource(
        source_identifier=adapter.source_identifier,
        name=adapter.source_name,
        base_url=adapter.base_url,
        adapter=type(adapter).__name__,
        access_method=(
            "api"
            if identifier == "codeforces"
            else "html"
        ),
        enabled=access_approved,
        access_notes=(
            access_notes
            or (
                "Access reviewed and approved."
                if access_approved
                else "Access policy review pending."
            )
        ),
    )

    return repository.create(source)