import asyncio

from datetime import datetime, timedelta, timezone

import pytest

from sqlalchemy import func, select

from app.core.enums import SourceHealth
from app.discovery.adapters.atcoder import AtCoderAdapter
from app.discovery.schemas import DiscoveryResult, RawEventCandidate
from app.discovery.source_registration import register_source
from app.models import Event, DiscoveryRun, ExtractionRecord
from app.services.discovery import DiscoveryService


def make_candidate(
    external_id="test-contest",
    title="Test Contest",
):
    start = datetime.now(timezone.utc) + timedelta(days=7)

    return RawEventCandidate(
        source_identifier="atcoder",
        external_id=external_id,
        title=title,
        source_url=(
            "https://atcoder.jp/contests/" + external_id
        ),
        raw_data={
            "phase": "upcoming",
            "starts_at": start.isoformat(),
            "duration_seconds": 6000,
        },
    )


@pytest.fixture
def enabled_source(db_session):

    source = register_source(
        db_session,
        "atcoder",
        access_approved=True,
        access_notes="Synthetic test fixture.",
    )

    db_session.commit()

    return source


@pytest.fixture
def successful_adapter(monkeypatch):

    candidate = make_candidate()

    async def fake_run(self, limit=20):

        return DiscoveryResult(
            source_identifier="atcoder",
            success=True,
            candidates=[candidate],
            request_count=1,
        )

    monkeypatch.setattr(
        AtCoderAdapter,
        "run",
        fake_run,
    )

    return candidate


def test_source_can_be_enabled(db_session):

    source = register_source(
        db_session,
        "atcoder",
    )

    assert source.enabled is False

    approved = register_source(
        db_session,
        "atcoder",
        access_approved=True,
    )

    assert approved.enabled is True
    assert approved.id == source.id


def test_unregistered_source(db_session):

    service = DiscoveryService(db_session)

    with pytest.raises(ValueError):

        asyncio.run(
            service.run_source("atcoder")
        )


def test_disabled_source(db_session):

    register_source(
        db_session,
        "atcoder",
    )

    with pytest.raises(ValueError):

        asyncio.run(
            DiscoveryService(
                db_session
            ).run_source("atcoder")
        )


def test_persistent_discovery(
    db_session,
    enabled_source,
    successful_adapter,
):

    result = asyncio.run(
        DiscoveryService(
            db_session
        ).run_source("atcoder")
    )

    assert result["status"] == "completed"
    assert result["inserted_count"] == 1
    assert result["discovered_count"] == 1


def test_discovery_run_saved(
    db_session,
    enabled_source,
    successful_adapter,
):

    asyncio.run(
        DiscoveryService(
            db_session
        ).run_source("atcoder")
    )

    run = db_session.scalar(
        select(DiscoveryRun)
    )

    assert run is not None
    assert run.completed_at is not None
    assert run.request_count == 1


def test_extraction_linked_to_run(
    db_session,
    enabled_source,
    successful_adapter,
):

    result = asyncio.run(
        DiscoveryService(
            db_session
        ).run_source("atcoder")
    )

    record = db_session.scalar(
        select(ExtractionRecord)
    )

    assert str(record.discovery_run_id) == result["run_id"]


def test_discovery_source_healthy(
    db_session,
    enabled_source,
    successful_adapter,
):

    asyncio.run(
        DiscoveryService(
            db_session
        ).run_source("atcoder")
    )

    db_session.refresh(enabled_source)

    assert enabled_source.health == SourceHealth.HEALTHY
    assert enabled_source.last_success_at is not None


def test_repeated_discovery(
    db_session,
    enabled_source,
    successful_adapter,
):

    service = DiscoveryService(db_session)

    first = asyncio.run(
        service.run_source("atcoder")
    )

    second = asyncio.run(
        service.run_source("atcoder")
    )

    assert first["inserted_count"] == 1
    assert second["inserted_count"] == 0
    assert second["duplicate_count"] == 1


def test_no_duplicate_events(
    db_session,
    enabled_source,
    successful_adapter,
):

    service = DiscoveryService(db_session)

    for _ in range(3):

        asyncio.run(
            service.run_source("atcoder")
        )

    count = db_session.scalar(
        select(func.count()).select_from(Event)
    )

    assert count == 1


def test_failed_source(
    db_session,
    enabled_source,
    monkeypatch,
):

    async def fake_run(self, limit=20):

        return DiscoveryResult(
            source_identifier="atcoder",
            success=False,
            error_code="ConnectTimeout",
            error_message="Network unavailable.",
            request_count=2,
            retry_count=1,
        )

    monkeypatch.setattr(
        AtCoderAdapter,
        "run",
        fake_run,
    )

    result = asyncio.run(
        DiscoveryService(
            db_session
        ).run_source("atcoder")
    )

    assert result["status"] == "failed"
    assert result["inserted_count"] == 0
    assert result["retry_count"] == 1

    db_session.refresh(enabled_source)

    assert enabled_source.health == SourceHealth.UNAVAILABLE


def test_partial_discovery(
    db_session,
    enabled_source,
    monkeypatch,
):

    valid = make_candidate(
        external_id="valid-contest",
    )

    invalid = make_candidate(
        external_id="invalid-contest",
        title="x" * 400,
    )

    async def fake_run(self, limit=20):

        return DiscoveryResult(
            source_identifier="atcoder",
            success=True,
            candidates=[valid, invalid],
        )

    monkeypatch.setattr(
        AtCoderAdapter,
        "run",
        fake_run,
    )

    result = asyncio.run(
        DiscoveryService(
            db_session
        ).run_source("atcoder")
    )

    assert result["status"] == "partial"
    assert result["inserted_count"] == 1
    assert result["failed_count"] == 1


def test_empty_discovery(
    db_session,
    enabled_source,
    monkeypatch,
):

    async def fake_run(self, limit=20):

        return DiscoveryResult(
            source_identifier="atcoder",
            success=True,
            candidates=[],
        )

    monkeypatch.setattr(
        AtCoderAdapter,
        "run",
        fake_run,
    )

    result = asyncio.run(
        DiscoveryService(
            db_session
        ).run_source("atcoder")
    )

    assert result["status"] == "completed"
    assert result["discovered_count"] == 0
    assert result["inserted_count"] == 0


def test_changed_content_not_duplicated(
    db_session,
    enabled_source,
    successful_adapter,
):

    service = DiscoveryService(db_session)

    asyncio.run(
        service.run_source("atcoder")
    )

    successful_adapter.title = "Updated Contest"

    result = asyncio.run(
        service.run_source("atcoder")
    )

    assert result["inserted_count"] == 0
    assert result["skipped_count"] == 1

    count = db_session.scalar(
        select(func.count()).select_from(Event)
    )

    assert count == 1