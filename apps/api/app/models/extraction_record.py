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

from app.core.enums import ExtractionMethod, ExtractionStatus
from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ExtractionRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "extraction_record"

    event_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("event.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    source_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("event_source.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    discovery_run_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("discovery_run.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    source_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    method: Mapped[ExtractionMethod] = mapped_column(
        SAEnum(
            ExtractionMethod,
            name="extraction_method",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        index=True,
    )

    status: Mapped[ExtractionStatus] = mapped_column(
        SAEnum(
            ExtractionStatus,
            name="extraction_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        index=True,
    )

    extracted_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    evidence: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    missing_fields: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    warnings: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    extractor_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    llm_provider: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    llm_model: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    completion_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    error_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    extracted_at: Mapped[datetime] = mapped_column(
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
            "content_hash IS NULL OR length(content_hash) = 64",
            name="valid_content_hash",
        ),
        CheckConstraint(
            "prompt_tokens IS NULL OR prompt_tokens >= 0",
            name="valid_prompt_tokens",
        ),
        CheckConstraint(
            "completion_tokens IS NULL OR completion_tokens >= 0",
            name="valid_completion_tokens",
        ),
        CheckConstraint(
            "duration_ms IS NULL OR duration_ms >= 0",
            name="valid_duration",
        ),
        Index(
            "ix_extraction_record_event_extracted",
            "event_id",
            "extracted_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ExtractionRecord("
            f"method={self.method}, "
            f"status={self.status})>"
        )