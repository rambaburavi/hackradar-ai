from datetime import datetime, timedelta, timezone

from app.core.enums import (
    EventCategory,
    EventLifecycleStatus,
    ExtractionMethod,
)

from app.discovery.schemas import RawEventCandidate
from app.discovery.urls import canonicalize_url

from app.extraction.schemas import ExtractedEvent

from app.schemas.event import EventCreate


class ExtractionEngine:

    def extract(
        self,
        candidate: RawEventCandidate,
    ) -> ExtractedEvent:

        if candidate.source_identifier not in {
            "atcoder",
            "codeforces",
        }:
            raise ValueError(
                "Unsupported extraction source."
            )

        raw = candidate.raw_data

        starts_at = None
        ends_at = None

        warnings = []

        start_value = raw.get("starts_at")

        if start_value:

            try:
                starts_at = datetime.fromisoformat(
                    start_value.replace("Z", "+00:00")
                )

                if starts_at.utcoffset() is None:
                    starts_at = None

                    warnings.append(
                        "Start time has no timezone."
                    )

                else:
                    starts_at = starts_at.astimezone(
                        timezone.utc
                    )

            except (ValueError, TypeError, AttributeError):

                warnings.append(
                    "Invalid start time."
                )

        duration = raw.get("duration_seconds")

        if (
            starts_at is not None
            and type(duration) is int
            and 0 < duration <= 31 * 86400
        ):

            ends_at = starts_at + timedelta(
                seconds=duration
            )

        lifecycle_status = (
            EventLifecycleStatus.UNKNOWN
        )

        if (
            starts_at is not None
            and starts_at > datetime.now(timezone.utc)
            and raw.get("phase") in {
                "BEFORE",
                "upcoming",
            }
        ):

            lifecycle_status = (
                EventLifecycleStatus.UPCOMING
            )

        source_url = canonicalize_url(
            str(candidate.source_url)
        )

        event = EventCreate(
            title=candidate.title,
            description=candidate.description,
            category=EventCategory.CODING_COMPETITION,
            official_url=source_url,
            starts_at=starts_at,
            ends_at=ends_at,
            lifecycle_status=lifecycle_status,
        )

        missing_fields = [
            field
            for field in (
                "description",
                "organizer",
                "registration_url",
                "registration_deadline",
                "registration_fee",
                "prize_amount",
                "starts_at",
                "ends_at",
            )
            if getattr(event, field) is None
        ]

        evidence = {
            "title": candidate.title,
            "official_url": source_url,
            "source_phase": raw.get("phase"),
            "starts_at": raw.get("starts_at"),
            "duration_seconds": duration,
        }

        return ExtractedEvent(
            source_identifier=(
                candidate.source_identifier
            ),
            external_id=candidate.external_id,
            canonical_url=source_url,
            event=event,
            extraction_method=(
                ExtractionMethod.API
                if candidate.source_identifier == "codeforces"
                else ExtractionMethod.HTML
            ),
            evidence=evidence,
            missing_fields=missing_fields,
            warnings=warnings,
        )