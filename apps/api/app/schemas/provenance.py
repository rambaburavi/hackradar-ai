from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import VerificationStatus
from app.schemas.event import EventRead


class EventSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    discovery_source_id: UUID
    external_id: str | None
    original_url: str
    canonical_url: str
    source_title: str | None

    first_discovered_at: datetime
    last_seen_at: datetime
    last_verified_at: datetime | None

    verification_status: VerificationStatus


class EligibilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_eligible: bool | None
    professional_eligible: bool | None
    graduate_eligible: bool | None

    graduation_year_min: int | None
    graduation_year_max: int | None

    allowed_graduation_years: list[int] | None

    age_min: int | None
    age_max: int | None

    allowed_degrees: list[str] | None
    allowed_disciplines: list[str] | None

    institution_restrictions: str | None

    allowed_countries: list[str] | None
    excluded_countries: list[str] | None
    allowed_states: list[str] | None

    geographical_restrictions: str | None

    required_skills: list[str] | None
    preferred_skills: list[str] | None

    min_experience_years: float | None
    max_experience_years: float | None

    experience_description: str | None

    individual_participation_allowed: bool | None
    team_participation_allowed: bool | None

    additional_requirements: str | None
    original_eligibility_text: str | None

    extraction_confidence: float | None


class VerificationLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: UUID
    source_id: UUID | None

    previous_status: str | None
    status: VerificationStatus

    verification_method: str

    confidence: float | None

    evidence: dict[str, Any] | list[Any] | None

    checked_fields: dict[str, Any] | list[Any] | None
    conflicting_fields: dict[str, Any] | list[Any] | None

    source_url: str | None
    http_status: int | None

    summary: str | None

    verified_at: datetime


class EventDetailRead(EventRead):
    sources: list[EventSourceRead]

    eligibility: EligibilityRead | None