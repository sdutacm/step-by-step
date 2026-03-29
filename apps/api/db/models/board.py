from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.group import Group
    from db.models.step import Step
    from db.models.user import User


class BoardVisibility(str, Enum):
    PUBLIC = "public"
    GROUP_MEMBER = "group_member"
    BOARD_USER = "board_user"


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[BoardVisibility] = mapped_column(
        default=BoardVisibility.BOARD_USER
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), index=True
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    step_id: Mapped[int] = mapped_column(
        ForeignKey("steps.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    group: Mapped["Group"] = relationship(back_populates="boards")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    step: Mapped["Step"] = relationship(back_populates="boards")
    board_users: Mapped[list["BoardUser"]] = relationship(
        back_populates="board",
        cascade="all, delete-orphan",
    )


class BoardUser(Base):
    __tablename__ = "board_users"
    __table_args__ = (UniqueConstraint("board_id", "user_id", name="uq_board_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    board_id: Mapped[int] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    board: Mapped["Board"] = relationship(back_populates="board_users")
    user: Mapped["User"] = relationship(back_populates="board_users")
