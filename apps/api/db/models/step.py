from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Step(Base):
    __tablename__ = "steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    creator: Mapped["User"] = relationship(back_populates="steps")
    group: Mapped["Group"] = relationship(back_populates="steps")
    step_problems: Mapped[list["StepProblem"]] = relationship(
        back_populates="step",
        cascade="all, delete-orphan",
        order_by="StepProblem.order",
    )
    board_step_users: Mapped[list["BoardStepUser"]] = relationship(
        back_populates="step",
        cascade="all, delete-orphan",
    )

    @property
    def problems(self) -> list["Problem"]:
        from db.models.problem import Problem

        return [sp.problem for sp in self.step_problems]

    @property
    def problem_count(self) -> int:
        return len(self.step_problems)
