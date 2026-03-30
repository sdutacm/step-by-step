"""remove_group_id_from_steps

Revision ID: f7ab4370f444
Revises: 57f9cfb5529b
Create Date: 2026-03-30 21:41:21.274651

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7ab4370f444"
down_revision: Union[str, None] = "57f9cfb5529b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("steps") as batch_op:
        batch_op.drop_index("ix_steps_group_id")
        batch_op.drop_column("group_id")


def downgrade() -> None:
    with op.batch_alter_table("steps") as batch_op:
        batch_op.add_column(sa.Column("group_id", sa.INTEGER(), nullable=True))
        batch_op.create_index("ix_steps_group_id", "group_id")
