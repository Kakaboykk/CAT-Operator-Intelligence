"""Rename downtime to downtime_minutes

Revision ID: 5b2b343daf80
Revises: ca83e8b0a3f2
Create Date: 2026-09-24 04:25:48.984592+00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b2b343daf80'
down_revision: Union[str, None] = 'ca83e8b0a3f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('machine_fault', 'downtime', new_column_name='downtime_minutes')

def downgrade() -> None:
    op.alter_column('machine_fault', 'downtime_minutes', new_column_name='downtime')
