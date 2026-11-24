from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import (
    DiscoveryRunStatus,
    SourceHealth,
)


class DiscoverySourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_identifier: str
    name: str
    description: str | None
    base_url: str
    adapter: str | None
    access_method: str | None
    enabled: bool
    health: SourceHealth

    last_attempt_at: datetime | None
    last_success_at: datetime | None
    last_failure_at: datetime | None

    consecutive_failures: int

    discovery_interval_minutes: int

    next_discovery_at: datetime | None

    created_at: datetime
    updated_at: datetime


class DiscoveryRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID

    trigger_type: str
    dry_run: bool

    requested_limit: int | None

    status: DiscoveryRunStatus

    started_at: datetime | None
    completed_at: datetime | None

    duration_ms: int | None

    discovered_count: int
    extracted_count: int
    inserted_count: int
    updated_count: int
    duplicate_count: int
    skipped_count: int
    failed_count: int

    request_count: int
    retry_count: int

    error_code: str | None

    created_at: datetime
    updated_at: datetime