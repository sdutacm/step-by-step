"""add is_temp to user and import_record table

Revision ID: 57f9cfb5529b
Revises: xxxxxxxxxxxx
Create Date: 2026-03-29 22:56:48.977344

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "57f9cfb5529b"
down_revision: Union[str, None] = "xxxxxxxxxxxx"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("is_temp", sa.Boolean(), nullable=False, server_default="0")
    )
    op.create_table(
        "import_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("imported_by", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("skip_count", sa.Integer(), nullable=False),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["imported_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_import_records_group_id"), "import_records", ["group_id"], unique=False
    )
    op.create_index(
        op.f("ix_import_records_id"), "import_records", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_import_records_source"), "import_records", ["source"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_import_records_source"), table_name="import_records")
    op.drop_index(op.f("ix_import_records_id"), table_name="import_records")
    op.drop_index(op.f("ix_import_records_group_id"), table_name="import_records")
    op.drop_table("import_records")
    op.drop_column("users", "is_temp")
