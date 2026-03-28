from db.base import Base
from sqlalchemy import Column, Integer, String, UniqueConstraint


class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(String, index=True)
    source = Column(String)
    title = Column(String)

    __table_args__ = (UniqueConstraint("source", "problem_id"),)
