from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from db.base import Base


class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(String, index=True)
    source = Column(String)
    title = Column(String)

    __table_args__ = (UniqueConstraint("source", "problem_id"),)

    solutions = relationship("Solution", back_populates="problem")
