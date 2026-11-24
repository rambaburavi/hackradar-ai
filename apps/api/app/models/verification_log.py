from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import VerificationStatus
from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class VerificationLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "verification_log"

    event_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("event.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("event_source.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    previous_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(
            VerificationStatus,
            name="verification_log_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=VerificationStatus.UNVERIFIED,
        server_default=VerificationStatus.UNVERIFIED.value,
        nullable=False,
        index=True,
    )

    verification_method: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    evidence: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    checked_fields: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    conflicting_fields: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    source_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    http_status: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1",
            name="valid_confidence",
        ),
        CheckConstraint(
            "http_status IS NULL OR http_status BETWEEN 100 AND 599",
            name="valid_http_status",
        ),
        CheckConstraint(
            "length(trim(verification_method)) > 0",
            name="non_empty_method",
        ),
        Index(
            "ix_verification_log_event_verified",
            "event_id",
            "verified_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<VerificationLog("
            f"event_id={self.event_id}, "
            f"status={self.status})>"
        )