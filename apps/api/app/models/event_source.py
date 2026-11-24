from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import VerificationStatus
from app.db.base import Base
from app.db.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class EventSource(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "event_source"

    # Parent event

    event_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "event.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Platform where the event was discovered

    discovery_source_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "discovery_source.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # External event identity

    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    original_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    canonical_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source_title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Content change detection

    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    etag: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    last_modified_header: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    # Additional source information

    source_metadata: Mapped[
        dict[str, Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Discovery timestamps

    first_discovered_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_fetched_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_verified_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Source-specific verification

    verification_status: Mapped[
        VerificationStatus
    ] = mapped_column(
        SAEnum(
            VerificationStatus,
            name="source_verification_status",
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

    last_fetch_error: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    # Constraints and indexes

    __table_args__ = (
        UniqueConstraint(
            "discovery_source_id",
            "external_id",
            name="uq_event_source_platform_external_id",
        ),
        
        CheckConstraint(
    "octet_length(canonical_url) <= 2000",
    name="canonical_url_max_bytes",
),

        UniqueConstraint(
            "discovery_source_id",
            "canonical_url",
            name="uq_event_source_platform_canonical_url",
        ),

        CheckConstraint(
            "length(trim(original_url)) > 0",
            name="non_empty_original_url",
        ),

        CheckConstraint(
            "length(trim(canonical_url)) > 0",
            name="non_empty_canonical_url",
        ),

        CheckConstraint(
            "external_id IS NULL "
            "OR length(trim(external_id)) > 0",
            name="valid_external_id",
        ),

        CheckConstraint(
            "content_hash IS NULL "
            "OR length(content_hash) = 64",
            name="valid_content_hash",
        ),

        Index(
            "ix_event_source_platform_last_seen",
            "discovery_source_id",
            "last_seen_at",
        ),

        Index(
            "ix_event_source_content_hash",
            "content_hash",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<EventSource("
            f"id={self.id}, "
            f"event_id={self.event_id}, "
            f"external_id={self.external_id!r}"
            f")>"
        )