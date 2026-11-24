import re
import unicodedata

from uuid import uuid4


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value or None


def normalize_title(title: str) -> str:
    cleaned = clean_text(title)

    if not cleaned:
        raise ValueError("Event title cannot be empty.")

    return cleaned.casefold()


def generate_slug(title: str) -> str:
    value = unicodedata.normalize("NFKD", title)

    value = value.encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    value = value.lower()

    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")[:280].rstrip("-")

    if not value:
        value = "event"

    return f"{value}-{uuid4().hex}"


def normalize_tag(value: str) -> str:
    cleaned = clean_text(value)

    if not cleaned:
        raise ValueError("Tag cannot be empty.")

    return re.sub(
        r"\s+",
        "-",
        cleaned.casefold(),
    )


def normalize_currency(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip().upper()

    if not re.fullmatch(r"[A-Z]{3}", value):
        raise ValueError(
            "Currency must be a three-letter code."
        )

    return value