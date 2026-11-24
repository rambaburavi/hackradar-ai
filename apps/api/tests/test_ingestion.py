from datetime import datetime, timedelta, timezone

import pytest

from sqlalchemy import func, select

from app.core.enums import (
    EventCategory,
    EventLifecycleStatus,
    VerificationStatus,
)

from app.discovery.schemas import RawEventCandidate

from app.discovery.source_registration import (
    register_source,
)

from app.extraction.engine import ExtractionEngine

from app.models import (
    Event,
    EventSource,
    ExtractionRecord,
)

from app.services.ingestion import IngestionService


def sample_candidate():

    start = (
        datetime.now(timezone.utc)
        + timedelta(days=7)
    )

    return RawEventCandidate(
        source_identifier="atcoder",
        external_id="test-abc",
        title="Test Programming Contest",
        source_url=(
            "https://atcoder.jp/contests/test-abc"
        ),
        raw_data={
            "phase": "upcoming",
            "starts_at": start.isoformat(),
            "duration_seconds": 6000,
        },
    )


@pytest.fixture
def approved_source(db_session):

    return register_source(
        db_session,
        "atcoder",
        access_approved=True,
    )


def test_extraction_title():

    result = ExtractionEngine().extract(
        sample_candidate()
    )

    assert result.event.title == (
        "Test Programming Contest"
    )


def test_extraction_category():

    result = ExtractionEngine().extract(
        sample_candidate()
    )

    assert result.event.category == (
        EventCategory.CODING_COMPETITION
    )


def test_extraction_start_time():

    result = ExtractionEngine().extract(
        sample_candidate()
    )

    assert result.event.starts_at is not None

    assert result.event.starts_at.utcoffset() == (
        timedelta(0)
    )


def test_extraction_end_time():

    result = ExtractionEngine().extract(
        sample_candidate()
    )

    assert (
        result.event.ends_at
        - result.event.starts_at
    ).total_seconds() == 6000


def test_extraction_upcoming_status():

    result = ExtractionEngine().extract(
        sample_candidate()
    )

    assert result.event.lifecycle_status == (
        EventLifecycleStatus.UPCOMING
    )


def test_extraction_unknown_fee():

    result = ExtractionEngine().extract(
        sample_candidate()
    )

    assert result.event.registration_fee is None


def test_extraction_unknown_deadline():

    result = ExtractionEngine().extract(
        sample_candidate()
    )

    assert result.event.registration_deadline is None


def test_extraction_missing_fields():

    result = ExtractionEngine().extract(
        sample_candidate()
    )

    assert "registration_deadline" in (
        result.missing_fields
    )


def test_invalid_start_time():

    candidate = sample_candidate()

    candidate.raw_data["starts_at"] = "unknown"

    result = ExtractionEngine().extract(candidate)

    assert result.event.starts_at is None
    assert result.event.ends_at is None


def test_naive_start_time():

    candidate = sample_candidate()

    candidate.raw_data["starts_at"] = (
        "2027-01-01T12:00:00"
    )

    result = ExtractionEngine().extract(candidate)

    assert result.event.starts_at is None


def test_invalid_duration():

    candidate = sample_candidate()

    candidate.raw_data["duration_seconds"] = -100

    result = ExtractionEngine().extract(candidate)

    assert result.event.ends_at is None


def test_source_disabled_by_default(db_session):

    source = register_source(
        db_session,
        "atcoder",
    )

    assert source.enabled is False


def test_source_registration_idempotent(db_session):

    first = register_source(
        db_session,
        "atcoder",
    )

    second = register_source(
        db_session,
        "atcoder",
    )

    assert first.id == second.id


def test_ingestion_disabled_source(db_session):

    register_source(
        db_session,
        "atcoder",
    )

    with pytest.raises(ValueError):

        IngestionService(db_session).ingest(
            sample_candidate()
        )


def test_ingestion_insert(
    db_session,
    approved_source,
):

    result = IngestionService(db_session).ingest(
        sample_candidate()
    )

    assert result["action"] == "inserted"

    assert result["event_id"]


def test_ingestion_duplicate(
    db_session,
    approved_source,
):

    service = IngestionService(db_session)

    candidate = sample_candidate()

    first = service.ingest(candidate)

    second = service.ingest(candidate)

    assert first["action"] == "inserted"

    assert second["action"] == "duplicate"

    assert first["event_id"] == second["event_id"]


def test_ingestion_no_duplicate_rows(
    db_session,
    approved_source,
):

    service = IngestionService(db_session)

    candidate = sample_candidate()

    for _ in range(3):

        service.ingest(candidate)

    count = db_session.scalar(
        select(func.count()).select_from(Event)
    )

    assert count == 1


def test_ingestion_source_provenance(
    db_session,
    approved_source,
):

    IngestionService(db_session).ingest(
        sample_candidate()
    )

    source = db_session.scalar(
        select(EventSource)
    )

    assert source.external_id == "test-abc"

    assert source.discovery_source_id == (
        approved_source.id
    )

    assert len(source.content_hash) == 64


def test_ingestion_extraction_record(
    db_session,
    approved_source,
):

    IngestionService(db_session).ingest(
        sample_candidate()
    )

    record = db_session.scalar(
        select(ExtractionRecord)
    )

    assert record is not None

    assert record.evidence["title"] == (
        "Test Programming Contest"
    )


def test_ingestion_unverified_by_default(
    db_session,
    approved_source,
):

    IngestionService(db_session).ingest(
        sample_candidate()
    )

    event = db_session.scalar(
        select(Event)
    )

    assert event.verification_status == (
        VerificationStatus.UNVERIFIED
    )


def test_ingestion_changed_content(
    db_session,
    approved_source,
):

    service = IngestionService(db_session)

    candidate = sample_candidate()

    service.ingest(candidate)

    candidate.title = "Updated Contest Title"

    result = service.ingest(candidate)

    assert result["action"] == "changed"

    count = db_session.scalar(
        select(func.count()).select_from(Event)
    )

    assert count == 1

    event = db_session.scalar(
        select(Event)
    )

    assert event.title == (
        "Test Programming Contest"
    )


def test_ingestion_transaction_rollback(
    db_session,
    approved_source,
):

    IngestionService(db_session).ingest(
        sample_candidate()
    )

    db_session.rollback()

    count = db_session.scalar(
        select(func.count()).select_from(Event)
    )

    assert count == 0