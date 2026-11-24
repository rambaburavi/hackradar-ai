from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ExtractionMethod
from app.schemas.event import EventCreate


class ExtractedEvent(BaseModel):

    model_config = ConfigDict(extra="forbid")

    source_identifier: str

    external_id: str | None = Field(
        default=None,
        max_length=255,
    )

    canonical_url: str = Field(
        min_length=1,
        max_length=2000,
    )

    event: EventCreate

    extraction_method: ExtractionMethod

    evidence: dict[str, Any] = Field(
        default_factory=dict
    )

    missing_fields: list[str] = Field(
        default_factory=list
    )

    warnings: list[str] = Field(
        default_factory=list
    )