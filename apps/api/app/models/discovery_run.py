from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    false,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import DiscoveryRunStatus
from app.db.base import Base
from app.db.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class DiscoveryRun(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "discovery_run"

    # --------------------------------------------------
    # Discovery platform
    # --------------------------------------------------

    source_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "discovery_source.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    # --------------------------------------------------
    # Execution configuration
    # --------------------------------------------------

    trigger_type: Mapped[str] = mapped_column(
        String(30),
        default="manual",
        server_default="manual",
        nullable=False,
        index=True,
    )

    dry_run: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
        nullable=False,
    )

    requested_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # --------------------------------------------------
    # Execution status
    # --------------------------------------------------

    status: Mapped[DiscoveryRunStatus] = mapped_column(
        SAEnum(
            DiscoveryRunStatus,
            name="discovery_run_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        default=DiscoveryRunStatus.PENDING,
        server_default=DiscoveryRunStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    # --------------------------------------------------
    # Execution timestamps
    # --------------------------------------------------

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # --------------------------------------------------
    # Discovery statistics
    # --------------------------------------------------

    discovered_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    extracted_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    inserted_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    updated_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    duplicate_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    skipped_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    failed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    # --------------------------------------------------
    # Network statistics
    # --------------------------------------------------

    request_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    # --------------------------------------------------
    # Error tracking
    # --------------------------------------------------

    error_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    error_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error_details: Mapped[
        dict[str, Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    # --------------------------------------------------
    # Additional execution metadata
    # --------------------------------------------------

    run_metadata: Mapped[
        dict[str, Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    # --------------------------------------------------
    # Database constraints and indexes
    # --------------------------------------------------

    __table_args__ = (
        CheckConstraint(
            "trigger_type IN "
            "('manual', 'scheduled', 'agent', 'retry')",
            name="valid_trigger_type",
        ),

        CheckConstraint(
            "requested_limit IS NULL "
            "OR requested_limit >= 1",
            name="valid_requested_limit",
        ),

        CheckConstraint(
            "duration_ms IS NULL OR duration_ms >= 0",
            name="valid_duration",
        ),

        CheckConstraint(
            "discovered_count >= 0",
            name="valid_discovered_count",
        ),

        CheckConstraint(
            "extracted_count >= 0",
            name="valid_extracted_count",
        ),

        CheckConstraint(
            "inserted_count >= 0",
            name="valid_inserted_count",
        ),

        CheckConstraint(
            "updated_count >= 0",
            name="valid_updated_count",
        ),

        CheckConstraint(
            "duplicate_count >= 0",
            name="valid_duplicate_count",
        ),

        CheckConstraint(
            "skipped_count >= 0",
            name="valid_skipped_count",
        ),

        CheckConstraint(
            "failed_count >= 0",
            name="valid_failed_count",
        ),

        CheckConstraint(
            "request_count >= 0",
            name="valid_request_count",
        ),

        CheckConstraint(
            "retry_count >= 0",
            name="valid_retry_count",
        ),

        CheckConstraint(
            "completed_at IS NULL "
            "OR (started_at IS NOT NULL "
            "AND completed_at >= started_at)",
            name="valid_execution_date_range",
        ),

        CheckConstraint(
            "status NOT IN ('completed', 'partial', 'failed') "
            "OR completed_at IS NOT NULL",
            name="terminal_status_requires_completion",
        ),

        CheckConstraint(
            "status != 'running' OR started_at IS NOT NULL",
            name="running_status_requires_start",
        ),

        CheckConstraint(
            "status NOT IN ('pending', 'running') "
            "OR completed_at IS NULL",
            name="active_status_without_completion",
        ),

        CheckConstraint(
            "NOT dry_run "
            "OR (inserted_count = 0 AND updated_count = 0)",
            name="dry_run_without_event_writes",
        ),

        Index(
            "ix_discovery_run_source_started",
            "source_id",
            "started_at",
        ),

        Index(
            "ix_discovery_run_status_started",
            "status",
            "started_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DiscoveryRun("
            f"id={self.id}, "
            f"source_id={self.source_id}, "
            f"status={self.status}, "
            f"discovered={self.discovered_count}"
            f")>"
        )