from datetime import timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

from lxml import etree


MAX_FEED_BYTES = 5_000_000


def parse_publication_date(value: str | None) -> str | None:

    if not value:
        return None

    try:
        date = parsedate_to_datetime(value)

        if date.tzinfo is None:
            return None

        return date.astimezone(timezone.utc).isoformat()

    except (ValueError, TypeError, OverflowError):
        return None


def is_valid_public_link(value: str) -> bool:

    try:
        parsed = urlsplit(value)

        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and parsed.port in (None, 443)
        )

    except ValueError:
        return False


def parse_rss(
    content: str | bytes,
    limit: int = 100,
) -> list[dict]:

    if isinstance(content, str):
        content = content.encode("utf-8")

    if len(content) > MAX_FEED_BYTES:
        raise ValueError("RSS feed exceeds size limit.")

    if limit < 1:
        raise ValueError("Limit must be positive.")

    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        recover=False,
        huge_tree=False,
    )

    root = etree.fromstring(content, parser=parser)

    if root.getroottree().docinfo.doctype:
        raise ValueError("RSS document types are not allowed.")

    if root.tag != "rss":
        raise ValueError("Expected an RSS document.")

    channel = root.find("channel")

    if channel is None:
        raise ValueError("RSS channel missing.")

    results = []
    seen = set()

    for item in channel.findall("item"):

        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or "").strip()

        description = (
            item.findtext("description") or ""
        ).strip()

        publication_date = parse_publication_date(
            item.findtext("pubDate")
        )

        categories = [
            category.text.strip()
            for category in item.findall("category")
            if category.text and category.text.strip()
        ]

        if not title or len(title) > 300:
            continue

        if not is_valid_public_link(link):
            continue

        identifier = guid or link

        if identifier in seen:
            continue

        seen.add(identifier)

        results.append({
            "title": title,
            "link": link,
            "guid": guid or None,
            "description": description or None,
            "published_at": publication_date,
            "categories": categories,
        })

        if len(results) >= limit:
            break

    return results