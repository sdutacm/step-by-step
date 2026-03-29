"""add created_by to groups

Revision ID: 8bc6fca4dff8
Revises: 3312fc310644
Create Date: 2026-03-29 19:17:30.910043

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "8bc6fca4dff8"
down_revision: Union[str, None] = "3312fc310644"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("groups", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("groups", recreate="always") as batch_op:
        batch_op.drop_column("created_by")
