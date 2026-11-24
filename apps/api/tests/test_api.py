from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import get_db
from app.main import app

from app.models import (
    DiscoveryRun,
    DiscoverySource,
    EligibilityCriteria,
    EventSource,
    VerificationLog,
)

from app.core.enums import VerificationStatus

from app.schemas.event import EventCreate
from app.services.event import EventService


BASE = "/api/v1"


@pytest.fixture
def client(db_session, monkeypatch):

    def override_get_db():
        yield db_session

    monkeypatch.setattr(
        settings,
        "ENABLE_DEV_MUTATIONS",
        False,
    )

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


def make_event(db_session, **overrides):
    values = {
        "title": "AI Hackathon",
        "category": "hackathon",
        "mode": "online",
    }

    values.update(overrides)

    return EventService(db_session).create_event(
        EventCreate(**values)
    )


def test_api_empty_events(client):
    response = client.get(f"{BASE}/events")

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []


def test_api_list_events(client, db_session):
    make_event(db_session)

    response = client.get(f"{BASE}/events")

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_api_search(client, db_session):
    make_event(
        db_session,
        title="Python AI Challenge",
    )

    make_event(
        db_session,
        title="Robotics Competition",
    )

    response = client.get(
        f"{BASE}/events",
        params={"search": "python"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_api_category_filter(client, db_session):
    make_event(db_session)

    make_event(
        db_session,
        category="robotics",
    )

    response = client.get(
        f"{BASE}/events",
        params={"category": "robotics"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_api_invalid_category(client):
    response = client.get(
        f"{BASE}/events",
        params={"category": "invalid"},
    )

    assert response.status_code == 422


def test_api_invalid_page_size(client):
    response = client.get(
        f"{BASE}/events",
        params={"page_size": 1000},
    )

    assert response.status_code == 422


def test_api_pagination(client, db_session):
    for i in range(5):
        make_event(
            db_session,
            title=f"Event {i}",
        )

    response = client.get(
        f"{BASE}/events",
        params={
            "page": 1,
            "page_size": 2,
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["total_pages"] == 3


def test_api_event_detail(client, db_session):
    event = make_event(db_session)

    response = client.get(
        f"{BASE}/events/{event.id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(event.id)
    assert response.json()["sources"] == []
    assert response.json()["eligibility"] is None


def test_api_event_not_found(client):
    response = client.get(
        f"{BASE}/events/{uuid4()}"
    )

    assert response.status_code == 404


def test_api_invalid_uuid(client):
    response = client.get(
        f"{BASE}/events/invalid-id"
    )

    assert response.status_code == 422


def test_api_upcoming_events(client, db_session):
    make_event(
        db_session,
        starts_at=(
            datetime.now(timezone.utc)
            + timedelta(days=10)
        ),
    )

    response = client.get(
        f"{BASE}/events/upcoming"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_api_deadlines(client, db_session):
    make_event(
        db_session,
        registration_deadline=(
            datetime.now(timezone.utc)
            + timedelta(days=3)
        ),
    )

    response = client.get(
        f"{BASE}/events/deadlines?days=7"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_api_invalid_deadline_days(client):
    response = client.get(
        f"{BASE}/events/deadlines?days=500"
    )

    assert response.status_code == 422


def test_api_create_disabled(client):
    response = client.post(
        f"{BASE}/events",
        json={"title": "Test Event"},
    )

    assert response.status_code == 404


def test_api_create_missing_key(client, monkeypatch):
    monkeypatch.setattr(
        settings,
        "ENABLE_DEV_MUTATIONS",
        True,
    )

    monkeypatch.setattr(
        settings,
        "DEV_API_KEY",
        "test-only-key",
    )

    response = client.post(
        f"{BASE}/events",
        json={"title": "Test Event"},
    )

    assert response.status_code == 403


def test_api_create_wrong_key(client, monkeypatch):
    monkeypatch.setattr(
        settings,
        "ENABLE_DEV_MUTATIONS",
        True,
    )

    monkeypatch.setattr(
        settings,
        "DEV_API_KEY",
        "test-only-key",
    )

    response = client.post(
        f"{BASE}/events",
        headers={
            "X-Dev-API-Key": "wrong-key",
        },
        json={"title": "Test Event"},
    )

    assert response.status_code == 403


def test_api_create_authorized(client, monkeypatch):
    monkeypatch.setattr(
        settings,
        "ENABLE_DEV_MUTATIONS",
        True,
    )

    monkeypatch.setattr(
        settings,
        "DEV_API_KEY",
        "test-only-key",
    )

    response = client.post(
        f"{BASE}/events",
        headers={
            "X-Dev-API-Key": "test-only-key",
        },
        json={
            "title": "Authorized Test Event",
            "category": "hackathon",
        },
    )

    assert response.status_code == 201

    assert response.json()["title"] == (
        "Authorized Test Event"
    )


def test_api_empty_sources(client):
    response = client.get(f"{BASE}/sources")

    assert response.status_code == 200
    assert response.json() == []


def test_api_source_detail(client, db_session):
    source = DiscoverySource(
        source_identifier="test-platform",
        name="Test Platform",
        base_url="https://example.com",
    )

    db_session.add(source)
    db_session.flush()

    response = client.get(
        f"{BASE}/sources/test-platform"
    )

    assert response.status_code == 200

    assert response.json()["name"] == (
        "Test Platform"
    )


def test_api_source_not_found(client):
    response = client.get(
        f"{BASE}/sources/unknown-platform"
    )

    assert response.status_code == 404


def test_api_empty_discovery_runs(client):
    response = client.get(
        f"{BASE}/discovery/runs"
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_api_discovery_run_detail(client, db_session):
    source = DiscoverySource(
        source_identifier="test-platform",
        name="Test Platform",
        base_url="https://example.com",
    )

    db_session.add(source)
    db_session.flush()

    run = DiscoveryRun(source_id=source.id)

    db_session.add(run)
    db_session.flush()

    response = client.get(
        f"{BASE}/discovery/runs/{run.id}"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_api_discovery_run_not_found(client):
    response = client.get(
        f"{BASE}/discovery/runs/{uuid4()}"
    )

    assert response.status_code == 404


def test_api_empty_verification_history(
    client,
    db_session,
):
    event = make_event(db_session)

    response = client.get(
        f"{BASE}/events/{event.id}/verification"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_api_verification_event_not_found(client):
    response = client.get(
        f"{BASE}/events/{uuid4()}/verification"
    )

    assert response.status_code == 404


def test_api_event_provenance(client, db_session):
    event = make_event(db_session)

    source = DiscoverySource(
        source_identifier="test-platform",
        name="Test Platform",
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

    db_session.add(
        EligibilityCriteria(
            event_id=event.id,
            student_eligible=True,
            allowed_graduation_years=[2027, 2028],
            required_skills=["python"],
        )
    )

    db_session.flush()

    response = client.get(
        f"{BASE}/events/{event.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["sources"]) == 1

    assert data["eligibility"]["student_eligible"] is True

    assert data["eligibility"]["required_skills"] == [
        "python"
    ]


def test_api_verification_history(client, db_session):
    event = make_event(db_session)

    log = VerificationLog(
        event_id=event.id,
        status=VerificationStatus.PARTIALLY_VERIFIED,
        verification_method="manual",
        confidence=0.7,
        evidence={"title": "AI Hackathon"},
    )

    db_session.add(log)
    db_session.flush()

    response = client.get(
        f"{BASE}/events/{event.id}/verification"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1

    assert response.json()[0]["status"] == (
        "partially_verified"
    )


def test_api_dashboard_stats(client, db_session):
    make_event(
        db_session,
        registration_fee=0,
    )

    response = client.get(f"{BASE}/stats")

    assert response.status_code == 200
    assert response.json()["total_events"] == 1
    assert response.json()["free_events"] == 1


def test_api_openapi_documentation(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert f"{BASE}/events" in paths
    assert f"{BASE}/stats" in paths
    assert f"{BASE}/sources" in paths
    assert f"{BASE}/discovery/runs" in paths