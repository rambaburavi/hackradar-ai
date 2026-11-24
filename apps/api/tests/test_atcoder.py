import pytest

from app.discovery.adapters.atcoder import (
    AtCoderAdapter,
)

from app.discovery.registry import (
    get_adapter,
    list_adapters,
)


SAMPLE_HTML = """
<html>
<body>

<div id="contest-table-upcoming">
<table>
<tbody>

<tr>
    <td>
        2027-01-10 21:00:00+0900
    </td>

    <td>
        <a href="/contests/abc999">
            AtCoder Beginner Contest 999
        </a>
    </td>

    <td>01:40</td>

    <td>~ 1999</td>
</tr>

<tr>
    <td>
        2027-01-15 21:00:00+0900
    </td>

    <td>
        <a href="/contests/arc999">
            AtCoder Regular Contest 999
        </a>
    </td>

    <td>02:00</td>

    <td>1200 ~ 2799</td>
</tr>

</tbody>
</table>
</div>

<div id="contest-table-action">
<table>
<tbody>
<tr>
    <td>2026-01-01 21:00:00+0900</td>
    <td>
        <a href="/contests/old-contest">
            Old Contest
        </a>
    </td>
    <td>02:00</td>
</tr>
</tbody>
</table>
</div>

</body>
</html>
"""


def test_atcoder_registered():

    assert "atcoder" in list_adapters()

    assert isinstance(
        get_adapter("atcoder"),
        AtCoderAdapter,
    )


def test_atcoder_parser():

    candidates = AtCoderAdapter().parse_response(
        SAMPLE_HTML,
        10,
    )

    assert len(candidates) == 2


def test_atcoder_external_id():

    candidate = AtCoderAdapter().parse_response(
        SAMPLE_HTML,
        10,
    )[0]

    assert candidate.external_id == "abc999"


def test_atcoder_title():

    candidate = AtCoderAdapter().parse_response(
        SAMPLE_HTML,
        10,
    )[0]

    assert candidate.title == (
        "AtCoder Beginner Contest 999"
    )


def test_atcoder_url():

    candidate = AtCoderAdapter().parse_response(
        SAMPLE_HTML,
        10,
    )[0]

    assert str(candidate.source_url) == (
        "https://atcoder.jp/contests/abc999"
    )


def test_atcoder_timezone_conversion():

    candidate = AtCoderAdapter().parse_response(
        SAMPLE_HTML,
        10,
    )[0]

    assert candidate.raw_data["starts_at"] == (
        "2027-01-10T12:00:00+00:00"
    )


def test_atcoder_duration():

    candidate = AtCoderAdapter().parse_response(
        SAMPLE_HTML,
        10,
    )[0]

    assert candidate.raw_data[
        "duration_seconds"
    ] == 6000


def test_atcoder_limit():

    candidates = AtCoderAdapter().parse_response(
        SAMPLE_HTML,
        1,
    )

    assert len(candidates) == 1


def test_atcoder_excludes_old_contests():

    candidates = AtCoderAdapter().parse_response(
        SAMPLE_HTML,
        10,
    )

    assert all(
        candidate.external_id != "old-contest"
        for candidate in candidates
    )


def test_atcoder_missing_section():

    with pytest.raises(ValueError):

        AtCoderAdapter().parse_response(
            "<html></html>",
            10,
        )


def test_atcoder_empty_section():

    html = """
    <div id="contest-table-upcoming">
        <table><tbody></tbody></table>
    </div>
    """

    assert AtCoderAdapter().parse_response(
        html,
        10,
    ) == []


def test_atcoder_invalid_datetime():

    assert AtCoderAdapter().parse_start_time(
        "unknown"
    ) is None


def test_atcoder_invalid_duration():

    assert AtCoderAdapter().parse_duration(
        "unknown"
    ) is None


def test_atcoder_no_fabricated_information():

    candidate = AtCoderAdapter().parse_response(
        SAMPLE_HTML,
        10,
    )[0]

    assert "registration_deadline" not in (
        candidate.raw_data
    )

    assert "registration_fee" not in (
        candidate.raw_data
    )

    assert "prize_amount" not in (
        candidate.raw_data
    )


def test_atcoder_duplicate_contests():

    html = SAMPLE_HTML.replace(
        "/contests/arc999",
        "/contests/abc999",
    )

    candidates = AtCoderAdapter().parse_response(
        html,
        10,
    )

    assert len(candidates) == 1