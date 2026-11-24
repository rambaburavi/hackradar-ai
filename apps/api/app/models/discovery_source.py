from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    Integer,
    String,
    Text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import SourceHealth
from app.db.base import Base
from app.db.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class DiscoverySource(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "discovery_source"

    # Platform identity

    source_identifier: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    base_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Discovery configuration

    adapter: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    access_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
        nullable=False,
        index=True,
    )

    access_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Source health

    health: Mapped[SourceHealth] = mapped_column(
        SAEnum(
            SourceHealth,
            name="source_health",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum: [
                item.value for item in enum
            ],
        ),
        default=SourceHealth.UNKNOWN,
        server_default=SourceHealth.UNKNOWN.value,
        nullable=False,
        index=True,
    )

    last_attempt_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_success_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_failure_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    consecutive_failures: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    last_error_summary: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    # Discovery scheduling configuration

    discovery_interval_minutes: Mapped[
        int
    ] = mapped_column(
        Integer,
        default=360,
        server_default="360",
        nullable=False,
    )

    next_discovery_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Database constraints

    __table_args__ = (
        CheckConstraint(
            "length(trim(source_identifier)) > 0",
            name="non_empty_identifier",
        ),

        CheckConstraint(
            "length(trim(name)) > 0",
            name="non_empty_name",
        ),

        CheckConstraint(
            "length(trim(base_url)) > 0",
            name="non_empty_base_url",
        ),

        CheckConstraint(
            "consecutive_failures >= 0",
            name="valid_failure_count",
        ),

        CheckConstraint(
            "discovery_interval_minutes >= 1",
            name="valid_discovery_interval",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DiscoverySource("
            f"identifier={self.source_identifier!r}, "
            f"health={self.health}"
            f")>"
        )