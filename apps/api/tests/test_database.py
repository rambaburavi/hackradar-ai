from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.core.enums import (
    DiscoveryRunStatus,
    EventCategory,
    EventLifecycleStatus,
    ExtractionMethod,
    ExtractionStatus,
    ParticipationMode,
    VerificationStatus,
)

from app.models import (
    DiscoveryRun,
    DiscoverySource,
    EligibilityCriteria,
    Event,
    EventSource,
    EventTag,
    ExtractionRecord,
    VerificationLog,
)


EXPECTED_TABLES = {
    "alembic_version",
    "event",
    "event_source",
    "discovery_source",
    "event_tag",
    "event_tag_link",
    "eligibility_criteria",
    "discovery_run",
    "verification_log",
    "extraction_record",
}


def create_event(**overrides):
    unique_id = uuid4().hex[:12]

    values = {
        "title": "Test AI Hackathon",
        "normalized_title": "test ai hackathon",
        "slug": f"test-ai-hackathon-{unique_id}",
        "category": EventCategory.HACKATHON,
        "mode": ParticipationMode.ONLINE,
    }

    values.update(overrides)

    return Event(**values)


def create_platform():
    return DiscoverySource(
        source_identifier=f"test-{uuid4().hex[:12]}",
        name="Test Platform",
        base_url="https://example.com",
    )


def test_database_connection(db_session):
    result = db_session.execute(
        text("SELECT 1")
    ).scalar_one()

    assert result == 1


def test_correct_database(db_session):
    database = db_session.execute(
        text("SELECT current_database()")
    ).scalar_one()

    assert database == "hackradar_test"


def test_all_database_tables_exist(test_engine):
    tables = set(inspect(test_engine).get_table_names())

    assert EXPECTED_TABLES.issubset(tables)


def test_migration_revision_exists(db_session):
    revision = db_session.execute(
        text("SELECT version_num FROM alembic_version")
    ).scalar_one()

    assert revision


def test_create_event(db_session):
    event = create_event()

    db_session.add(event)
    db_session.commit()

    event_id = event.id

    db_session.expire_all()

    saved = db_session.get(Event, event_id)

    assert saved is not None
    assert saved.title == "Test AI Hackathon"
    assert saved.category == EventCategory.HACKATHON
    assert saved.mode == ParticipationMode.ONLINE


def test_event_defaults(db_session):
    event = create_event()

    db_session.add(event)
    db_session.flush()

    assert event.id is not None
    assert event.created_at is not None
    assert event.updated_at is not None

    assert (
        event.lifecycle_status
        == EventLifecycleStatus.UNKNOWN
    )

    assert (
        event.verification_status
        == VerificationStatus.UNVERIFIED
    )


def test_update_event(db_session):
    event = create_event()

    db_session.add(event)
    db_session.flush()

    event.title = "Updated AI Hackathon"
    event.normalized_title = "updated ai hackathon"

    db_session.commit()
    db_session.refresh(event)

    assert event.title == "Updated AI Hackathon"


def test_delete_event(db_session):
    event = create_event()

    db_session.add(event)
    db_session.flush()

    event_id = event.id

    db_session.delete(event)
    db_session.commit()

    assert db_session.get(Event, event_id) is None


def test_unique_event_slug(db_session):
    event = create_event()

    db_session.add(event)
    db_session.flush()

    duplicate = create_event(slug=event.slug)

    db_session.add(duplicate)

    with pytest.raises(IntegrityError):
        db_session.flush()

    db_session.rollback()


def test_negative_registration_fee_rejected(db_session):
    event = create_event(
        registration_fee=Decimal("-100.00")
    )

    db_session.add(event)

    with pytest.raises(IntegrityError):
        db_session.flush()

    db_session.rollback()


def test_invalid_team_size_rejected(db_session):
    event = create_event(
        min_team_size=5,
        max_team_size=2,
    )

    db_session.add(event)

    with pytest.raises(IntegrityError):
        db_session.flush()

    db_session.rollback()


def test_invalid_event_dates_rejected(db_session):
    now = datetime.now(timezone.utc)

    event = create_event(
        starts_at=now,
        ends_at=now - timedelta(days=1),
    )

    db_session.add(event)

    with pytest.raises(IntegrityError):
        db_session.flush()

    db_session.rollback()


def test_invalid_confidence_rejected(db_session):
    event = create_event(
        verification_confidence=1.5
    )

    db_session.add(event)

    with pytest.raises(IntegrityError):
        db_session.flush()

    db_session.rollback()


def test_unknown_fee_is_not_free(db_session):
    unknown_fee = create_event(
        registration_fee=None
    )

    free_event = create_event(
        registration_fee=Decimal("0.00")
    )

    db_session.add_all([unknown_fee, free_event])
    db_session.flush()

    db_session.refresh(unknown_fee)
    db_session.refresh(free_event)

    assert unknown_fee.registration_fee is None
    assert free_event.registration_fee == Decimal("0.00")


def test_event_source_persistence(db_session):
    event = create_event()
    platform = create_platform()

    source = EventSource(
        discovery_source=platform,
        external_id="test-001",
        original_url="https://example.com/event",
        canonical_url="https://example.com/event",
        source_metadata={
            "category": "AI",
            "featured": True,
        },
    )

    event.sources.append(source)

    db_session.add(event)
    db_session.commit()

    db_session.expire_all()

    saved = db_session.get(Event, event.id)

    assert len(saved.sources) == 1
    assert saved.sources[0].external_id == "test-001"

    assert saved.sources[0].source_metadata == {
        "category": "AI",
        "featured": True,
    }


def test_duplicate_source_rejected(db_session):
    event = create_event()
    platform = create_platform()

    source_one = EventSource(
        discovery_source=platform,
        external_id="duplicate-001",
        original_url="https://example.com/event",
        canonical_url="https://example.com/event",
    )

    source_two = EventSource(
        discovery_source=platform,
        external_id="duplicate-001",
        original_url="https://example.com/event",
        canonical_url="https://example.com/event",
    )

    event.sources.extend([source_one, source_two])

    db_session.add(event)

    with pytest.raises(IntegrityError):
        db_session.flush()

    db_session.rollback()


def test_event_tags_persistence(db_session):
    event = create_event()

    tag = EventTag(
        normalized_name=f"python-{uuid4().hex[:8]}",
        display_name="Python",
        category="programming_language",
    )

    event.tags.append(tag)

    db_session.add(event)
    db_session.commit()

    db_session.expire_all()

    saved = db_session.get(Event, event.id)

    assert len(saved.tags) == 1
    assert saved.tags[0].display_name == "Python"


def test_eligibility_persistence(db_session):
    event = create_event()

    event.eligibility = EligibilityCriteria(
        student_eligible=True,
        allowed_graduation_years=[2027, 2028],
        allowed_countries=["IN"],
        required_skills=["python"],
    )

    db_session.add(event)
    db_session.commit()

    db_session.expire_all()

    saved = db_session.get(Event, event.id)

    assert saved.eligibility.student_eligible is True

    assert saved.eligibility.allowed_graduation_years == [
        2027,
        2028,
    ]

    assert saved.eligibility.allowed_countries == ["IN"]


def test_invalid_eligibility_range(db_session):
    event = create_event()

    event.eligibility = EligibilityCriteria(
        graduation_year_min=2028,
        graduation_year_max=2026,
    )

    db_session.add(event)

    with pytest.raises(IntegrityError):
        db_session.flush()

    db_session.rollback()


def test_discovery_run_persistence(db_session):
    platform = create_platform()

    now = datetime.now(timezone.utc)

    run = DiscoveryRun(
        source=platform,
        status=DiscoveryRunStatus.COMPLETED,
        started_at=now - timedelta(seconds=10),
        completed_at=now,
        duration_ms=10000,
        discovered_count=20,
        extracted_count=20,
        inserted_count=10,
        updated_count=5,
        duplicate_count=5,
    )

    db_session.add(run)
    db_session.commit()

    db_session.refresh(run)

    assert run.status == DiscoveryRunStatus.COMPLETED
    assert run.discovered_count == 20
    assert run.inserted_count == 10


def test_invalid_dry_run_rejected(db_session):
    platform = create_platform()

    run = DiscoveryRun(
        source=platform,
        dry_run=True,
        inserted_count=5,
    )

    db_session.add(run)

    with pytest.raises(IntegrityError):
        db_session.flush()

    db_session.rollback()


def test_verification_log_persistence(db_session):
    event = create_event()

    verification = VerificationLog(
        status=VerificationStatus.PARTIALLY_VERIFIED,
        verification_method="structured_data",
        confidence=0.85,
        evidence={
            "title": {
                "matched": True,
            }
        },
    )

    event.verification_logs.append(verification)

    db_session.add(event)
    db_session.commit()

    db_session.expire_all()

    saved = db_session.get(Event, event.id)

    assert len(saved.verification_logs) == 1

    assert (
        saved.verification_logs[0].confidence
        == pytest.approx(0.85)
    )


def test_extraction_record_persistence(db_session):
    event = create_event()

    extraction = ExtractionRecord(
        method=ExtractionMethod.HTML,
        status=ExtractionStatus.SUCCESS,
        extracted_data={
            "title": "Test AI Hackathon",
        },
        confidence=0.90,
    )

    event.extraction_records.append(extraction)

    db_session.add(event)
    db_session.commit()

    db_session.expire_all()

    saved = db_session.get(Event, event.id)

    assert len(saved.extraction_records) == 1

    assert (
        saved.extraction_records[0].method
        == ExtractionMethod.HTML
    )


def test_failed_extraction_without_event(db_session):
    record = ExtractionRecord(
        method=ExtractionMethod.HTML,
        status=ExtractionStatus.FAILED,
        source_url="https://example.com/event",
        error_code="PARSING_FAILED",
    )

    db_session.add(record)
    db_session.commit()

    db_session.refresh(record)

    assert record.id is not None
    assert record.event_id is None


def test_event_delete_cascades(db_session):
    event = create_event()
    platform = create_platform()

    source = EventSource(
        discovery_source=platform,
        original_url="https://example.com/event",
        canonical_url="https://example.com/event",
    )

    event.sources.append(source)

    event.eligibility = EligibilityCriteria(
        student_eligible=True
    )

    db_session.add(event)
    db_session.flush()

    event_id = event.id
    source_id = source.id
    eligibility_id = event.eligibility.id
    platform_id = platform.id

    db_session.delete(event)
    db_session.commit()

    assert db_session.get(Event, event_id) is None

    assert db_session.get(
        EventSource,
        source_id,
    ) is None

    assert db_session.get(
        EligibilityCriteria,
        eligibility_id,
    ) is None

    assert db_session.get(
        DiscoverySource,
        platform_id,
    ) is not None


def test_event_search_query(db_session):
    event = create_event(
        title="Generative AI Innovation Challenge",
        normalized_title="generative ai innovation challenge",
    )

    db_session.add(event)
    db_session.flush()

    statement = select(Event).where(
        Event.normalized_title.contains("generative ai")
    )

    results = db_session.scalars(statement).all()

    assert event in results