from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.solution import Solution
    from db.models.step_problem import StepProblem


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    problem_id: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("source", "problem_id"),)

    solutions: Mapped[list["Solution"]] = relationship(back_populates="problem")
    step_problems: Mapped[list["StepProblem"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan"
    )
