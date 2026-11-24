from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from pydantic import ValidationError

from app.core.enums import (
    EventCategory,
    EventLifecycleStatus,
    ParticipationMode,
)

from app.models import (
    DiscoveryRun,
    DiscoverySource,
    EventSource,
)

from app.repositories.discovery_run import (
    DiscoveryRunRepository,
)

from app.repositories.discovery_source import (
    DiscoverySourceRepository,
)

from app.schemas.event import (
    EventCreate,
    EventFilters,
)

from app.services.event import EventService
from app.services.stats import StatsService

from app.utils.normalization import (
    clean_text,
    generate_slug,
    normalize_currency,
    normalize_tag,
    normalize_title,
)


def create_test_event(db_session, **overrides):
    values = {
        "title": "AI Hackathon",
        "category": EventCategory.HACKATHON,
        "mode": ParticipationMode.ONLINE,
    }

    values.update(overrides)

    return EventService(db_session).create_event(
        EventCreate(**values)
    )


def test_clean_text():
    assert clean_text("  AI    Hackathon  ") == (
        "AI Hackathon"
    )


def test_empty_text():
    assert clean_text("   ") is None


def test_normalize_title():
    assert normalize_title(" AI HACKATHON ") == (
        "ai hackathon"
    )


def test_normalize_tag():
    assert normalize_tag("Machine Learning") == (
        "machine-learning"
    )


def test_unique_slug():
    first = generate_slug("AI Hackathon")
    second = generate_slug("AI Hackathon")

    assert first.startswith("ai-hackathon-")
    assert first != second


def test_normalize_currency():
    assert normalize_currency("inr") == "INR"


def test_invalid_currency():
    with pytest.raises(ValueError):
        normalize_currency("rupees")


def test_invalid_empty_title():
    with pytest.raises(ValidationError):
        EventCreate(title="   ")


def test_invalid_fee():
    with pytest.raises(ValidationError):
        EventCreate(
            title="Test",
            registration_fee=-100,
        )


def test_invalid_team_range():
    with pytest.raises(ValidationError):
        EventCreate(
            title="Test",
            min_team_size=5,
            max_team_size=2,
        )


def test_naive_datetime_rejected():
    with pytest.raises(ValidationError):
        EventCreate(
            title="Test",
            starts_at=datetime(2027, 1, 1),
        )


def test_invalid_url():
    with pytest.raises(ValidationError):
        EventCreate(
            title="Test",
            official_url="javascript:alert(1)",
        )


def test_invalid_page_size():
    with pytest.raises(ValidationError):
        EventFilters(page_size=1000)


def test_create_event_service(db_session):
    event = create_test_event(db_session)

    assert event.id is not None
    assert event.normalized_title == "ai hackathon"
    assert event.slug.startswith("ai-hackathon-")


def test_get_event_service(db_session):
    event = create_test_event(db_session)

    result = EventService(db_session).get_event(
        event.id
    )

    assert result is not None
    assert result.id == event.id


def test_event_not_found(db_session):
    result = EventService(db_session).get_event(
        uuid4()
    )

    assert result is None


def test_search_events(db_session):
    create_test_event(
        db_session,
        title="Generative AI Hackathon",
    )

    create_test_event(
        db_session,
        title="Robotics Challenge",
    )

    result = EventService(db_session).list_events(
        EventFilters(search="generative ai")
    )

    assert result.total == 1

    assert result.items[0].title == (
        "Generative AI Hackathon"
    )


def test_search_wildcard_is_literal(db_session):
    create_test_event(
        db_session,
        title="Python Challenge",
    )

    result = EventService(db_session).list_events(
        EventFilters(search="%")
    )

    assert result.total == 0


def test_category_filter(db_session):
    create_test_event(db_session)

    create_test_event(
        db_session,
        title="Robotics Competition",
        category=EventCategory.ROBOTICS,
    )

    result = EventService(db_session).list_events(
        EventFilters(
            category=EventCategory.ROBOTICS
        )
    )

    assert result.total == 1


def test_mode_filter(db_session):
    create_test_event(db_session)

    create_test_event(
        db_session,
        mode=ParticipationMode.OFFLINE,
    )

    result = EventService(db_session).list_events(
        EventFilters(
            mode=ParticipationMode.ONLINE
        )
    )

    assert result.total == 1


def test_country_filter(db_session):
    create_test_event(
        db_session,
        country="India",
    )

    create_test_event(
        db_session,
        country="USA",
    )

    result = EventService(db_session).list_events(
        EventFilters(country="india")
    )

    assert result.total == 1


def test_free_fee_filter(db_session):
    create_test_event(
        db_session,
        registration_fee=0,
    )

    create_test_event(
        db_session,
        registration_fee=None,
    )

    create_test_event(
        db_session,
        registration_fee=500,
    )

    result = EventService(db_session).list_events(
        EventFilters(fee_type="free")
    )

    assert result.total == 1


def test_unknown_fee_filter(db_session):
    create_test_event(
        db_session,
        registration_fee=None,
    )

    create_test_event(
        db_session,
        registration_fee=0,
    )

    result = EventService(db_session).list_events(
        EventFilters(fee_type="unknown")
    )

    assert result.total == 1


def test_pagination(db_session):
    for index in range(5):
        create_test_event(
            db_session,
            title=f"Event {index}",
        )

    result = EventService(db_session).list_events(
        EventFilters(
            page=1,
            page_size=2,
        )
    )

    assert result.total == 5
    assert len(result.items) == 2
    assert result.total_pages == 3
    assert result.has_next is True


def test_title_sorting(db_session):
    create_test_event(
        db_session,
        title="Zebra Hackathon",
    )

    create_test_event(
        db_session,
        title="Alpha Hackathon",
    )

    result = EventService(db_session).list_events(
        EventFilters(sort_by="title")
    )

    assert result.items[0].title == (
        "Alpha Hackathon"
    )


def test_upcoming_events(db_session):
    now = datetime.now(timezone.utc)

    create_test_event(
        db_session,
        starts_at=now + timedelta(days=10),
    )

    create_test_event(
        db_session,
        starts_at=now - timedelta(days=10),
    )

    result = EventService(
        db_session
    ).get_upcoming()

    assert len(result) == 1


def test_deadline_filter(db_session):
    now = datetime.now(timezone.utc)

    create_test_event(
        db_session,
        registration_deadline=(
            now + timedelta(days=3)
        ),
    )

    create_test_event(
        db_session,
        registration_deadline=(
            now + timedelta(days=20)
        ),
    )

    result = EventService(
        db_session
    ).get_deadlines(days=7)

    assert len(result) == 1


def test_cancelled_event_excluded(db_session):
    create_test_event(
        db_session,
        starts_at=(
            datetime.now(timezone.utc)
            + timedelta(days=10)
        ),
        lifecycle_status=(
            EventLifecycleStatus.CANCELLED
        ),
    )

    result = EventService(
        db_session
    ).get_upcoming()

    assert len(result) == 0


def test_discovery_source_repository(db_session):
    repository = DiscoverySourceRepository(
        db_session
    )

    source = repository.create(
        DiscoverySource(
            source_identifier="test-platform",
            name="Test Platform",
            base_url="https://example.com",
        )
    )

    result = repository.get_by_identifier(
        "test-platform"
    )

    assert result is not None
    assert result.id == source.id


def test_discovery_run_repository(db_session):
    source = DiscoverySource(
        source_identifier="test-run-platform",
        name="Test Run Platform",
        base_url="https://example.com",
    )

    db_session.add(source)
    db_session.flush()

    repository = DiscoveryRunRepository(
        db_session
    )

    run = repository.create(
        DiscoveryRun(source_id=source.id)
    )

    results, total = repository.list_runs(
        source_id=source.id
    )

    assert total == 1
    assert results[0].id == run.id


def test_source_filter(db_session):
    event = create_test_event(db_session)

    create_test_event(
        db_session,
        title="Unrelated Event",
    )

    source = DiscoverySource(
        source_identifier="test-source-filter",
        name="Test Source",
        base_url="https://example.com",
    )

    db_session.add(source)
    db_session.flush()

    db_session.add(
        EventSource(
            event_id=event.id,
            discovery_source_id=source.id,
            original_url="https://example.com/event",
            canonical_url="https://example.com/event",
        )
    )

    db_session.flush()

    result = EventService(db_session).list_events(
        EventFilters(source="test-source-filter")
    )

    assert result.total == 1
    assert result.items[0].id == event.id


def test_empty_dashboard_stats(db_session):
    stats = StatsService(
        db_session
    ).get_stats()

    assert stats.total_events == 0
    assert stats.total_sources == 0


def test_dashboard_stats(db_session):
    create_test_event(
        db_session,
        registration_fee=0,
        registration_deadline=(
            datetime.now(timezone.utc)
            + timedelta(days=3)
        ),
    )

    stats = StatsService(
        db_session
    ).get_stats()

    assert stats.total_events == 1
    assert stats.free_events == 1
    assert stats.deadlines_next_7_days == 1