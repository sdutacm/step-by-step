from sqlalchemy import Column, Integer, String
from db.base import Base


class SourceUser(Base):
    __tablename__ = "source_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    source = Column(String)
