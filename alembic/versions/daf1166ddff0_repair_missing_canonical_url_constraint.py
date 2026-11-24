"""repair missing canonical URL constraint

Revision ID: daf1166ddff0
Revises: 789a2ca52859
Create Date: 2026-11-24 20:08:56.339235

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'daf1166ddff0'
down_revision: Union[str, Sequence[str], None] = '789a2ca52859'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'ck_event_source_canonical_url_max_bytes'
                AND conrelid = 'event_source'::regclass
            ) THEN
                ALTER TABLE event_source
                ADD CONSTRAINT ck_event_source_canonical_url_max_bytes
                CHECK (octet_length(canonical_url) <= 2000);
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    # Preserve the constraint required by the previous revision.
    pass