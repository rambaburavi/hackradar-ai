import pytest

from lxml import etree

from app.discovery.parsers.rss import (
    parse_rss,
    parse_publication_date,
)

from app.discovery.adapters.hackclub import (
    HackClubAdapter,
)


SAMPLE_RSS = """
<rss version="2.0">
    <channel>
        <title>Synthetic Event Feed</title>

        <item>
            <title>Test Hackathon</title>
            <link>https://test.hackclub.com</link>
            <guid>test-event-001</guid>
            <pubDate>Mon, 23 Nov 2026 16:51:39 GMT</pubDate>
            <description>Build a software project.</description>
            <category>Software</category>
        </item>

        <item>
            <title>Second Event</title>
            <link>https://second.hackclub.com</link>
            <guid>test-event-002</guid>
            <category>ongoing</category>
        </item>

    </channel>
</rss>
"""


def test_parse_rss_items():

    result = parse_rss(SAMPLE_RSS)

    assert len(result) == 2


def test_rss_title():

    result = parse_rss(SAMPLE_RSS)

    assert result[0]["title"] == "Test Hackathon"


def test_rss_guid():

    result = parse_rss(SAMPLE_RSS)

    assert result[0]["guid"] == "test-event-001"


def test_rss_publication_date():

    result = parse_rss(SAMPLE_RSS)

    assert result[0]["published_at"] == (
        "2026-11-23T16:51:39+00:00"
    )


def test_rss_categories():

    result = parse_rss(SAMPLE_RSS)

    assert result[0]["categories"] == ["Software"]


def test_missing_publication_date():

    result = parse_rss(SAMPLE_RSS)

    assert result[1]["published_at"] is None


def test_invalid_publication_date():

    assert parse_publication_date("invalid") is None


def test_rss_limit():

    assert len(parse_rss(SAMPLE_RSS, limit=1)) == 1


def test_invalid_limit():

    with pytest.raises(ValueError):

        parse_rss(SAMPLE_RSS, limit=0)


def test_duplicate_rss_items():

    duplicate = SAMPLE_RSS.replace(
        "test-event-002",
        "test-event-001",
    )

    assert len(parse_rss(duplicate)) == 1


def test_invalid_xml():

    with pytest.raises(etree.XMLSyntaxError):

        parse_rss("<rss>")


def test_empty_feed():

    assert parse_rss(
        "<rss><channel></channel></rss>"
    ) == []


def test_non_rss_document():

    with pytest.raises(ValueError):

        parse_rss("<html></html>")


def test_xml_doctype_rejected():

    content = """
    <!DOCTYPE rss [
        <!ENTITY example SYSTEM "file:///example.txt">
    ]>
    <rss>
        <channel>
            <title>&example;</title>
        </channel>
    </rss>
    """

    with pytest.raises(ValueError):

        parse_rss(content)


def test_oversized_feed():

    with pytest.raises(ValueError):

        parse_rss(b"x" * 5_000_001)


def test_unsafe_url():

    content = SAMPLE_RSS.replace(
        "https://test.hackclub.com",
        "javascript:alert(1)",
    )

    assert len(parse_rss(content)) == 1


def test_adapter_candidates():

    candidates = HackClubAdapter.parse(SAMPLE_RSS)

    assert len(candidates) == 2

    assert candidates[0].source_identifier == "hackclub"


def test_adapter_external_id():

    candidates = HackClubAdapter.parse(SAMPLE_RSS)

    assert candidates[0].external_id == "test-event-001"


def test_adapter_rejects_external_domain():

    content = SAMPLE_RSS.replace(
        "https://test.hackclub.com",
        "https://example.com",
    )

    assert len(HackClubAdapter.parse(content)) == 1


def test_publication_not_event_start():

    candidates = HackClubAdapter.parse(SAMPLE_RSS)

    assert "starts_at" not in candidates[0].raw_data

    assert "registration_deadline" not in candidates[0].raw_data