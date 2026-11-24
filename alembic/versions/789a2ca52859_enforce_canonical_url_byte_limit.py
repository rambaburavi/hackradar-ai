"""enforce canonical URL byte limit

Revision ID: 789a2ca52859
Revises: 077804336292
Create Date: 2026-11-24 20:04:06.791273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '789a2ca52859'
down_revision: Union[str, Sequence[str], None] = '077804336292'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        op.f("ck_event_source_canonical_url_max_bytes"),
        "event_source",
        "octet_length(canonical_url) <= 2000",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_event_source_canonical_url_max_bytes"),
        "event_source",
        type_="check",
    )
