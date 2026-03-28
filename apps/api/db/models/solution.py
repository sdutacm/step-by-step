from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from db.base import Base
from schemas.language import LanguageEnum
from schemas.result import ResultEnum


class Solution(Base):
    __tablename__ = "solutions"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    nickname = Column(String)
    source = Column(String)
    result = Column(Enum(ResultEnum))
    language = Column(Enum(LanguageEnum))
    submitted_at = Column(DateTime, index=True)
    solution_id = Column(Integer, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), index=True)

    problem = relationship("Problem", back_populates="solutions")
