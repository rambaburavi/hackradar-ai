from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import (
    EventCategory,
    EventLifecycleStatus,
    ParticipationMode,
    VerificationStatus,
)
from app.db.base import Base
from app.db.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


# Association table for the many-to-many relationship
# between events and tags.
event_tag_link = Table(
    "event_tag_link",
    Base.metadata,
    Column(
        "event_id",
        Uuid(as_uuid=True),
        ForeignKey("event.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        Uuid(as_uuid=True),
        ForeignKey("event_tag.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Index("ix_event_tag_link_tag_id", "tag_id"),
)


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):

    __tablename__ = "event"

    # --------------------------------------------------
    # Basic event information
    # --------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    normalized_title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(350),
        nullable=False,
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    organizer: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
        index=True,
    )

    category: Mapped[EventCategory] = mapped_column(
        SAEnum(
            EventCategory,
            name="event_category",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        default=EventCategory.UNKNOWN,
        server_default=EventCategory.UNKNOWN.value,
        nullable=False,
        index=True,
    )

    # --------------------------------------------------
    # Participation and location
    # --------------------------------------------------

    mode: Mapped[ParticipationMode] = mapped_column(
        SAEnum(
            ParticipationMode,
            name="participation_mode",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        default=ParticipationMode.UNKNOWN,
        server_default=ParticipationMode.UNKNOWN.value,
        nullable=False,
        index=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    state: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    venue: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # --------------------------------------------------
    # Official URLs
    # --------------------------------------------------

    official_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    registration_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # --------------------------------------------------
    # Important dates
    # --------------------------------------------------

    registration_opens_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    registration_deadline: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    original_timezone: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # --------------------------------------------------
    # Financial information
    # --------------------------------------------------

    registration_fee: Mapped[
        Decimal | None
    ] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    currency: Mapped[str | None] = mapped_column(
        String(3),
        nullable=True,
    )

    prize_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(16, 2),
        nullable=True,
    )

    prize_currency: Mapped[str | None] = mapped_column(
        String(3),
        nullable=True,
    )

    prize_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # --------------------------------------------------
    # Team requirements
    # --------------------------------------------------

    min_team_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    max_team_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # --------------------------------------------------
    # Event lifecycle
    # --------------------------------------------------

    lifecycle_status: Mapped[
        EventLifecycleStatus
    ] = mapped_column(
        SAEnum(
            EventLifecycleStatus,
            name="event_lifecycle_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        default=EventLifecycleStatus.UNKNOWN,
        server_default=EventLifecycleStatus.UNKNOWN.value,
        nullable=False,
        index=True,
    )

    # --------------------------------------------------
    # Verification information
    # --------------------------------------------------

    verification_status: Mapped[
        VerificationStatus
    ] = mapped_column(
        SAEnum(
            VerificationStatus,
            name="verification_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        default=VerificationStatus.UNVERIFIED,
        server_default=VerificationStatus.UNVERIFIED.value,
        nullable=False,
        index=True,
    )

    verification_confidence: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # --------------------------------------------------
    # Discovery and freshness
    # --------------------------------------------------

    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_verified_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # --------------------------------------------------
    # Database constraints and indexes
    # --------------------------------------------------

    __table_args__ = (
        CheckConstraint(
            "length(trim(title)) > 0",
            name="non_empty_title",
        ),

        CheckConstraint(
            "length(trim(normalized_title)) > 0",
            name="non_empty_normalized_title",
        ),

        CheckConstraint(
            "length(trim(slug)) > 0",
            name="non_empty_slug",
        ),

        CheckConstraint(
            "registration_fee IS NULL "
            "OR registration_fee >= 0",
            name="non_negative_registration_fee",
        ),

        CheckConstraint(
            "prize_amount IS NULL OR prize_amount >= 0",
            name="non_negative_prize_amount",
        ),

        CheckConstraint(
            "min_team_size IS NULL OR min_team_size >= 1",
            name="valid_min_team_size",
        ),

        CheckConstraint(
            "max_team_size IS NULL OR max_team_size >= 1",
            name="valid_max_team_size",
        ),

        CheckConstraint(
            "min_team_size IS NULL "
            "OR max_team_size IS NULL "
            "OR max_team_size >= min_team_size",
            name="valid_team_size_range",
        ),

        CheckConstraint(
            "starts_at IS NULL "
            "OR ends_at IS NULL "
            "OR ends_at >= starts_at",
            name="valid_event_date_range",
        ),

        CheckConstraint(
            "registration_opens_at IS NULL "
            "OR registration_deadline IS NULL "
            "OR registration_deadline >= registration_opens_at",
            name="valid_registration_date_range",
        ),

        CheckConstraint(
            "verification_confidence IS NULL "
            "OR verification_confidence BETWEEN 0 AND 1",
            name="valid_verification_confidence",
        ),

        Index(
            "ix_event_status_deadline",
            "lifecycle_status",
            "registration_deadline",
        ),

        Index(
            "ix_event_category_mode",
            "category",
            "mode",
        ),

        Index(
            "ix_event_location",
            "country",
            "state",
            "city",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Event("
            f"id={self.id}, "
            f"title={self.title!r}, "
            f"status={self.lifecycle_status}"
            f")>"
        )