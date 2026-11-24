from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

from app.core.enums import (
    EventCategory,
    EventLifecycleStatus,
    ParticipationMode,
    VerificationStatus,
)

from app.utils.normalization import (
    clean_text,
    normalize_currency,
)


class EventBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=300)

    description: str | None = Field(
        default=None,
        max_length=100000,
    )

    organizer: str | None = Field(
        default=None,
        max_length=300,
    )

    category: EventCategory = EventCategory.UNKNOWN

    mode: ParticipationMode = ParticipationMode.UNKNOWN

    country: str | None = Field(
        default=None,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        max_length=150,
    )

    city: str | None = Field(
        default=None,
        max_length=150,
    )

    venue: str | None = Field(
        default=None,
        max_length=500,
    )

    official_url: HttpUrl | None = None

    registration_url: HttpUrl | None = None

    registration_opens_at: datetime | None = None

    registration_deadline: datetime | None = None

    starts_at: datetime | None = None

    ends_at: datetime | None = None

    original_timezone: str | None = Field(
        default=None,
        max_length=100,
    )

    registration_fee: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=14,
        decimal_places=2,
    )

    currency: str | None = None

    prize_amount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=16,
        decimal_places=2,
    )

    prize_currency: str | None = None

    prize_description: str | None = Field(
        default=None,
        max_length=10000,
    )

    min_team_size: int | None = Field(
        default=None,
        ge=1,
    )

    max_team_size: int | None = Field(
        default=None,
        ge=1,
    )

    lifecycle_status: EventLifecycleStatus = (
        EventLifecycleStatus.UNKNOWN
    )

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value):
        if not isinstance(value, str):
            raise ValueError("Title must be a string.")

        cleaned = clean_text(value)

        if not cleaned:
            raise ValueError("Title cannot be empty.")

        return cleaned

    @field_validator("currency", "prize_currency")
    @classmethod
    def validate_currency(cls, value):
        return normalize_currency(value)

    @field_validator(
        "registration_opens_at",
        "registration_deadline",
        "starts_at",
        "ends_at",
    )
    @classmethod
    def validate_datetime(cls, value):
        if value is None:
            return None

        if value.utcoffset() is None:
            raise ValueError(
                "Datetime must include timezone information."
            )

        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_ranges(self):
        if (
            self.min_team_size is not None
            and self.max_team_size is not None
            and self.min_team_size > self.max_team_size
        ):
            raise ValueError("Invalid team size range.")

        if (
            self.starts_at is not None
            and self.ends_at is not None
            and self.ends_at < self.starts_at
        ):
            raise ValueError("Invalid event date range.")

        if (
            self.registration_opens_at is not None
            and self.registration_deadline is not None
            and self.registration_deadline
            < self.registration_opens_at
        ):
            raise ValueError(
                "Invalid registration date range."
            )

        return self


class EventCreate(EventBase):
    pass


class EventTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    normalized_name: str
    display_name: str
    category: str | None


class EventRead(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    normalized_title: str

    slug: str

    verification_status: VerificationStatus

    verification_confidence: float | None

    discovered_at: datetime

    last_verified_at: datetime | None

    created_at: datetime

    updated_at: datetime

    tags: list[EventTagRead] = Field(
        default_factory=list
    )


class EventFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    search: str | None = Field(
        default=None,
        max_length=200,
    )

    category: EventCategory | None = None

    mode: ParticipationMode | None = None

    country: str | None = Field(
        default=None,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        max_length=150,
    )

    city: str | None = Field(
        default=None,
        max_length=150,
    )

    lifecycle_status: EventLifecycleStatus | None = None

    verification_status: VerificationStatus | None = None

    source: str | None = Field(
        default=None,
        max_length=100,
    )

    fee_type: Literal[
        "free",
        "paid",
        "unknown",
    ] | None = None

    deadline_within_days: int | None = Field(
        default=None,
        ge=1,
        le=365,
    )

    sort_by: Literal[
        "newest",
        "oldest",
        "deadline",
        "start_date",
        "title",
    ] = "newest"

    page: int = Field(default=1, ge=1, le=10000)

    page_size: int = Field(default=20, ge=1, le=100)