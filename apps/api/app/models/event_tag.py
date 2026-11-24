from sqlalchemy import (
    CheckConstraint,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class EventTag(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "event_tag"

    # Normalized tag identifier

    normalized_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    # Human-readable tag name

    display_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    # Tag classification

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Optional description

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Database constraints

    __table_args__ = (
        CheckConstraint(
            "length(trim(normalized_name)) > 0",
            name="non_empty_normalized_name",
        ),

        CheckConstraint(
            "length(trim(display_name)) > 0",
            name="non_empty_display_name",
        ),

        CheckConstraint(
            "normalized_name = lower(trim(normalized_name))",
            name="normalized_name_format",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<EventTag("
            f"name={self.normalized_name!r}, "
            f"category={self.category!r}"
            f")>"
        )