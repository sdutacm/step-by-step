"""drop group_step_progress table

Revision ID: xxxxxxxxxxxx
Revises: 4528061ea8ec
Create Date: 2026-03-29 20:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "xxxxxxxxxxxx"
down_revision: Union[str, None] = "4528061ea8ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(
        op.f("ix_group_step_progress_user_id"), table_name="group_step_progress"
    )
    op.drop_index(
        op.f("ix_group_step_progress_step_id"), table_name="group_step_progress"
    )
    op.drop_index(
        op.f("ix_group_step_progress_problem_id"), table_name="group_step_progress"
    )
    op.drop_index(op.f("ix_group_step_progress_id"), table_name="group_step_progress")
    op.drop_index(
        op.f("ix_group_step_progress_group_id"), table_name="group_step_progress"
    )
    op.drop_table("group_step_progress")


def downgrade() -> None:
    op.create_table(
        "group_step_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("step_id", sa.Integer(), nullable=False),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("ac_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["step_id"], ["steps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "group_id",
            "user_id",
            "step_id",
            "problem_id",
            name="uq_group_user_step_problem",
        ),
    )
    op.create_index(
        op.f("ix_group_step_progress_group_id"),
        "group_step_progress",
        ["group_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_group_step_progress_id"), "group_step_progress", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_group_step_progress_problem_id"),
        "group_step_progress",
        ["problem_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_group_step_progress_step_id"),
        "group_step_progress",
        ["step_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_group_step_progress_user_id"),
        "group_step_progress",
        ["user_id"],
        unique=False,
    )
