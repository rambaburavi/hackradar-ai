import json

import pytest

from app.discovery.adapters.codeforces import (
    CodeforcesAdapter,
)

from app.discovery.registry import (
    get_adapter,
    list_adapters,
)

from app.discovery.urls import (
    UnsafeURL,
    canonicalize_url,
    validate_source_url,
)


def test_canonical_url_tracking_removal():

    result = canonicalize_url(
        "https://example.com/event"
        "?id=10&utm_source=test#section"
    )

    assert result == (
        "https://example.com/event?id=10"
    )


def test_canonical_url_preserves_path():

    assert canonicalize_url(
        "https://example.com/Event"
    ) == "https://example.com/Event"


def test_allowed_source():

    url = "https://codeforces.com/api/contest.list"

    assert validate_source_url(
        url,
        {"codeforces.com"},
    ) == url


@pytest.mark.parametrize(
    "url",
    [
        "http://codeforces.com",
        "https://localhost",
        "https://127.0.0.1",
        "https://192.168.1.1",
        "https://evil.example",
        "https://codeforces.com.evil.example",
        "https://codeforces.com:8080",
        "https://user:password@codeforces.com",
    ],
)
def test_unsafe_source_rejected(url):

    with pytest.raises(UnsafeURL):

        validate_source_url(
            url,
            {"codeforces.com"},
        )


def test_long_canonical_url_rejected():

    with pytest.raises(UnsafeURL):

        canonicalize_url(
            "https://example.com/" + "x" * 3000
        )


def test_registry():

    assert "codeforces" in list_adapters()

    assert isinstance(
        get_adapter("codeforces"),
        CodeforcesAdapter,
    )


def test_unknown_adapter():

    with pytest.raises(ValueError):
        get_adapter("unknown")


def sample_response():

    return json.dumps({
        "status": "OK",
        "result": [
            {
                "id": 100,
                "name": "Upcoming Test Contest",
                "phase": "BEFORE",
                "type": "CF",
                "startTimeSeconds": 1800000000,
                "durationSeconds": 7200,
            },
            {
                "id": 101,
                "name": "Completed Test Contest",
                "phase": "FINISHED",
            },
        ],
    })


def test_codeforces_parser():

    adapter = CodeforcesAdapter()

    candidates = adapter.parse_response(
        sample_response(),
        20,
    )

    assert len(candidates) == 1

    assert candidates[0].external_id == "100"

    assert candidates[0].title == (
        "Upcoming Test Contest"
    )


def test_codeforces_source_url():

    candidate = CodeforcesAdapter().parse_response(
        sample_response(),
        20,
    )[0]

    assert str(candidate.source_url) == (
        "https://codeforces.com/contest/100"
    )


def test_codeforces_failed_response():

    with pytest.raises(ValueError):

        CodeforcesAdapter().parse_response(
            '{"status":"FAILED"}',
            20,
        )


def test_codeforces_empty_response():

    result = CodeforcesAdapter().parse_response(
        '{"status":"OK","result":[]}',
        20,
    )

    assert result == []


def test_codeforces_missing_fields():

    result = CodeforcesAdapter().parse_response(
        json.dumps({
            "status": "OK",
            "result": [
                {"phase": "BEFORE"}
            ],
        }),
        20,
    )

    assert result == []


def test_codeforces_limit():

    result = CodeforcesAdapter().parse_response(
        sample_response(),
        0,
    )

    assert result == []


def test_codeforces_no_fabricated_deadline():

    candidate = CodeforcesAdapter().parse_response(
        sample_response(),
        20,
    )[0]

    assert "registration_deadline" not in (
        candidate.raw_data
    )

    assert "prize_amount" not in (
        candidate.raw_data
    )