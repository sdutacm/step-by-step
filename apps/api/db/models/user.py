from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.source_user import SourceUser
    from db.models.step import Step


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column()
    nickname: Mapped[str | None] = mapped_column(nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(nullable=True)

    source_users: Mapped[list["SourceUser"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    steps: Mapped[list["Step"]] = relationship(back_populates="creator")
