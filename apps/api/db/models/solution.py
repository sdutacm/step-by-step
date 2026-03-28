from db.base import Base
from schemas.language import LanguageEnum
from schemas.result import ResultEnum
from sqlalchemy import Column, DateTime, Enum, Integer, String


class Solution(Base):
    __tablename__ = "solutions"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    nickname = Column(String)
    source = Column(String)
    result = Column(Enum(ResultEnum))
    language = Column(Enum(LanguageEnum))
    submitted_at = Column(DateTime, index=True)
