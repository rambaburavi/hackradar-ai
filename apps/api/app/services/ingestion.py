import hashlib
import json
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.enums import ExtractionStatus

from app.discovery.schemas import RawEventCandidate

from app.extraction.engine import ExtractionEngine

from app.models import (
    Event,
    EventSource,
    ExtractionRecord,
)

from app.repositories.discovery_source import (
    DiscoverySourceRepository,
)

from app.repositories.event_source import (
    EventSourceRepository,
)

from app.utils.normalization import (
    generate_slug,
    normalize_title,
)


class IngestionService:

    def __init__(self, db: Session):

        self.db = db

        self.extractor = ExtractionEngine()

        self.sources = DiscoverySourceRepository(db)

        self.event_sources = EventSourceRepository(db)

    def ingest(
    self,
    candidate: RawEventCandidate,
    discovery_run_id: UUID | None = None,
) -> dict:

        extracted = self.extractor.extract(candidate)

        platform = self.sources.get_by_identifier(
            extracted.source_identifier
        )

        if platform is None or not platform.enabled:
            raise ValueError(
                "Discovery source is not enabled."
            )

        if platform.access_method not in {
            "api",
            "html",
            "rss",
        }:
            raise ValueError(
                "Discovery access is not configured."
            )

        now = datetime.now(timezone.utc)

        content = json.dumps(
            {
                "title": candidate.title,
                "description": candidate.description,
                "raw_data": candidate.raw_data,
            },
            sort_keys=True,
            ensure_ascii=False,
        )

        content_hash = hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

        existing = None

        if extracted.external_id:

            existing = (
                self.event_sources.find_by_external_id(
                    platform.id,
                    extracted.external_id,
                )
            )

        by_url = self.event_sources.find_by_url(
            platform.id,
            extracted.canonical_url,
        )

        if (
            existing is not None
            and by_url is not None
            and existing.id != by_url.id
        ):
            raise ValueError(
                "Conflicting source identities."
            )

        existing = existing or by_url

        if existing is not None:

            existing.last_seen_at = now

            if existing.content_hash == content_hash:

                self.db.flush()

                return {
                    "action": "duplicate",
                    "event_id": str(existing.event_id),
                }

            # Changed content is recorded for review.
            # Do not overwrite previously verified fields.

            existing.content_hash = content_hash

            existing.source_metadata = candidate.raw_data

            self.db.add(
                ExtractionRecord(
                    event_id=existing.event_id,
                    source_id=existing.id,
                    discovery_run_id=discovery_run_id,
                    source_url=extracted.canonical_url,
                    method=extracted.extraction_method,
                    status=ExtractionStatus.PARTIAL,
                    extracted_data=(
                        extracted.event.model_dump(
                            mode="json"
                        )
                    ),
                    evidence=extracted.evidence,
                    missing_fields=extracted.missing_fields,
                    warnings=[
                        *extracted.warnings,
                        "Changed source content requires review.",
                    ],
                    content_hash=content_hash,
                )
            )

            self.db.flush()

            return {
                "action": "changed",
                "event_id": str(existing.event_id),
            }

        values = extracted.event.model_dump()

        for field in (
            "official_url",
            "registration_url",
        ):

            if values[field] is not None:

                values[field] = str(values[field])

        event = Event(
            **values,
            normalized_title=normalize_title(
                extracted.event.title
            ),
            slug=generate_slug(
                extracted.event.title
            ),
        )

        self.db.add(event)

        self.db.flush()

        source = EventSource(
            event_id=event.id,
            discovery_source_id=platform.id,
            external_id=extracted.external_id,
            original_url=str(candidate.source_url),
            canonical_url=extracted.canonical_url,
            source_title=candidate.title,
            source_metadata=candidate.raw_data,
            content_hash=content_hash,
            last_seen_at=now,
        )

        self.db.add(source)

        self.db.flush()

        record = ExtractionRecord(
            event_id=event.id,
            source_id=source.id,
            source_url=extracted.canonical_url,
            discovery_run_id=discovery_run_id,
            method=extracted.extraction_method,
            status=(
                ExtractionStatus.PARTIAL
                if extracted.missing_fields
                else ExtractionStatus.SUCCESS
            ),
            extracted_data=(
                extracted.event.model_dump(
                    mode="json"
                )
            ),
            evidence=extracted.evidence,
            missing_fields=extracted.missing_fields,
            warnings=extracted.warnings,
            content_hash=content_hash,
        )

        self.db.add(record)

        self.db.flush()

        return {
            "action": "inserted",
            "event_id": str(event.id),
        }