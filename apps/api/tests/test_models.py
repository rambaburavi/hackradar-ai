from datetime import datetime, timezone

from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import configure_mappers
from sqlalchemy.schema import CreateIndex, CreateTable

from app.core.enums import (
    DiscoveryRunStatus,
    EventCategory,
    ExtractionMethod,
    ExtractionStatus,
    ParticipationMode,
    VerificationStatus,
)
from app.db.base import Base
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


def test_all_tables_registered():
    assert set(Base.metadata.tables.keys()) == EXPECTED_TABLES


def test_foreign_keys_resolve():
    for table in Base.metadata.tables.values():
        for foreign_key in table.foreign_keys:
            assert foreign_key.column is not None


def test_metadata_dependency_order():
    tables = Base.metadata.sorted_tables
    assert len(tables) == 9


def test_postgresql_ddl_compilation():
    dialect = postgresql.dialect()

    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=dialect))
        assert "CREATE TABLE" in ddl

        for index in table.indexes:
            ddl = str(CreateIndex(index).compile(dialect=dialect))
            assert "INDEX" in ddl


def test_all_mappers_configure():
    configure_mappers()

    assert len(Base.registry.mappers) == 8


def test_event_relationships():
    relationships = inspect(Event).relationships

    assert relationships["sources"].uselist is True
    assert relationships["eligibility"].uselist is False
    assert relationships["tags"].uselist is True
    assert relationships["verification_logs"].uselist is True
    assert relationships["extraction_records"].uselist is True


def test_source_relationships():
    relationships = inspect(DiscoverySource).relationships

    assert relationships["event_sources"].uselist is True
    assert relationships["discovery_runs"].uselist is True


def test_complete_event_object_graph():
    configure_mappers()

    platform = DiscoverySource(
        source_identifier="test-platform",
        name="Test Platform",
        base_url="https://example.com",
    )

    event = Event(
        title="AI Innovation Hackathon",
        normalized_title="ai innovation hackathon",
        slug="ai-innovation-hackathon",
        category=EventCategory.HACKATHON,
        mode=ParticipationMode.ONLINE,
    )

    source = EventSource(
        discovery_source=platform,
        external_id="test-001",
        original_url="https://example.com/event",
        canonical_url="https://example.com/event",
    )

    event.sources.append(source)

    tag = EventTag(
        normalized_name="artificial-intelligence",
        display_name="Artificial Intelligence",
        category="technology",
    )

    event.tags.append(tag)

    event.eligibility = EligibilityCriteria(
        student_eligible=True,
        allowed_graduation_years=[2027, 2028],
        required_skills=["python"],
    )

    run = DiscoveryRun(
        source=platform,
        status=DiscoveryRunStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
    )

    verification = VerificationLog(
        source=source,
        status=VerificationStatus.PARTIALLY_VERIFIED,
        verification_method="structured_data",
        confidence=0.75,
    )

    event.verification_logs.append(verification)

    extraction = ExtractionRecord(
        source=source,
        discovery_run=run,
        method=ExtractionMethod.HTML,
        status=ExtractionStatus.SUCCESS,
        extracted_data={"title": event.title},
        confidence=0.85,
    )

    event.extraction_records.append(extraction)

    assert source.event is event
    assert source.discovery_source is platform

    assert event.eligibility.event is event
    assert event in tag.events

    assert source in platform.event_sources
    assert run in platform.discovery_runs

    assert verification.event is event
    assert verification in source.verification_logs

    assert extraction.event is event
    assert extraction in source.extraction_records
    assert extraction in run.extraction_records


def test_unknown_eligibility_is_preserved():
    criteria = EligibilityCriteria()

    assert criteria.student_eligible is None
    assert criteria.professional_eligible is None
    assert criteria.allowed_countries is None


def test_eligibility_event_is_unique():
    assert EligibilityCriteria.__table__.c.event_id.unique is True


def test_extraction_can_fail_before_event_creation():
    record = ExtractionRecord(
        source_url="https://example.com/event",
        method=ExtractionMethod.HTML,
        status=ExtractionStatus.FAILED,
        error_code="EXTRACTION_FAILED",
    )

    assert record.event_id is None
    assert record.status == ExtractionStatus.FAILED