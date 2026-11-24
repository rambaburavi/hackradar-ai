from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class EligibilityCriteria(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "eligibility_criteria"

    # Parent event

    event_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "event.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    # Participant categories

    student_eligible: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    professional_eligible: Mapped[
        bool | None
    ] = mapped_column(
        Boolean,
        nullable=True,
    )

    graduate_eligible: Mapped[
        bool | None
    ] = mapped_column(
        Boolean,
        nullable=True,
    )

    # Graduation requirements

    graduation_year_min: Mapped[
        int | None
    ] = mapped_column(
        Integer,
        nullable=True,
    )

    graduation_year_max: Mapped[
        int | None
    ] = mapped_column(
        Integer,
        nullable=True,
    )

    allowed_graduation_years: Mapped[
        list[int] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Age requirements

    age_min: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    age_max: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Educational requirements

    allowed_degrees: Mapped[
        list[str] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    allowed_disciplines: Mapped[
        list[str] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    institution_restrictions: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    # Geographic restrictions

    allowed_countries: Mapped[
        list[str] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    excluded_countries: Mapped[
        list[str] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    allowed_states: Mapped[
        list[str] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    geographical_restrictions: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    # Technical requirements

    required_skills: Mapped[
        list[str] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    preferred_skills: Mapped[
        list[str] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Professional experience

    min_experience_years: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    max_experience_years: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    experience_description: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    # Team participation

    individual_participation_allowed: Mapped[
        bool | None
    ] = mapped_column(
        Boolean,
        nullable=True,
    )

    team_participation_allowed: Mapped[
        bool | None
    ] = mapped_column(
        Boolean,
        nullable=True,
    )

    # Additional restrictions

    additional_requirements: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    # Original source information

    original_eligibility_text: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    extraction_confidence: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    # Database constraints

    __table_args__ = (
        CheckConstraint(
            "graduation_year_min IS NULL "
            "OR graduation_year_min BETWEEN 1900 AND 2200",
            name="valid_min_graduation_year",
        ),

        CheckConstraint(
            "graduation_year_max IS NULL "
            "OR graduation_year_max BETWEEN 1900 AND 2200",
            name="valid_max_graduation_year",
        ),

        CheckConstraint(
            "graduation_year_min IS NULL "
            "OR graduation_year_max IS NULL "
            "OR graduation_year_max >= graduation_year_min",
            name="valid_graduation_year_range",
        ),

        CheckConstraint(
            "age_min IS NULL OR age_min BETWEEN 0 AND 130",
            name="valid_min_age",
        ),

        CheckConstraint(
            "age_max IS NULL OR age_max BETWEEN 0 AND 130",
            name="valid_max_age",
        ),

        CheckConstraint(
            "age_min IS NULL "
            "OR age_max IS NULL "
            "OR age_max >= age_min",
            name="valid_age_range",
        ),

        CheckConstraint(
            "min_experience_years IS NULL "
            "OR min_experience_years >= 0",
            name="valid_min_experience",
        ),

        CheckConstraint(
            "max_experience_years IS NULL "
            "OR max_experience_years >= 0",
            name="valid_max_experience",
        ),

        CheckConstraint(
            "min_experience_years IS NULL "
            "OR max_experience_years IS NULL "
            "OR max_experience_years >= min_experience_years",
            name="valid_experience_range",
        ),

        CheckConstraint(
            "extraction_confidence IS NULL "
            "OR extraction_confidence BETWEEN 0 AND 1",
            name="valid_extraction_confidence",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<EligibilityCriteria("
            f"event_id={self.event_id}, "
            f"student_eligible={self.student_eligible}"
            f")>"
        )