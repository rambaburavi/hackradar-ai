from datetime import datetime, timezone
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
)


class RawEventCandidate(BaseModel):

    model_config = ConfigDict(extra="forbid")

    source_identifier: str

    external_id: str | None = None

    title: str = Field(
        min_length=1,
        max_length=500,
    )

    source_url: HttpUrl

    description: str | None = None

    raw_data: dict[str, Any] = Field(
        default_factory=dict
    )

    discovered_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


class DiscoveryResult(BaseModel):

    source_identifier: str

    success: bool

    candidates: list[RawEventCandidate] = Field(
        default_factory=list
    )

    request_count: int = 0

    retry_count: int = 0

    duration_ms: int = 0

    warnings: list[str] = Field(
        default_factory=list
    )

    error_code: str | None = None

    error_message: str | None = None


class DiscoverySummary(BaseModel):

    total_sources: int

    successful_sources: int

    failed_sources: int

    total_candidates: int

    results: list[DiscoveryResult]