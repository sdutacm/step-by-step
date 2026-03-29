from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.group import Group
    from db.models.problem import Problem
    from db.models.step import Step
    from db.models.user import User


class GroupStepProgress(Base):
    __tablename__ = "group_step_progress"
    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "user_id",
            "step_id",
            "problem_id",
            name="uq_group_user_step_problem",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    step_id: Mapped[int] = mapped_column(
        ForeignKey("steps.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[int] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), index=True
    )
    ac_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    group: Mapped["Group"] = relationship()
    user: Mapped["User"] = relationship()
    step: Mapped["Step"] = relationship()
    problem: Mapped["Problem"] = relationship()
