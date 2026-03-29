from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class StepProblem(Base):
    __tablename__ = "step_problems"
    __table_args__ = (
        UniqueConstraint("step_id", "problem_id", name="uq_step_problem"),
    )

    step_id: Mapped[int] = mapped_column(
        ForeignKey("steps.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    problem_id: Mapped[int] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    order: Mapped[int] = mapped_column(Integer, default=0)
    specialty: Mapped[str | None] = mapped_column(String, nullable=True)
    topic: Mapped[str | None] = mapped_column(String, nullable=True)

    step: Mapped["Step"] = relationship(back_populates="step_problems")
    problem: Mapped["Problem"] = relationship(back_populates="step_problems")
