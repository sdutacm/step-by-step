from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

if TYPE_CHECKING:
    from db.models.group import Group
    from db.models.user import User


class GroupRole(str, Enum):
    MEMBER = "member"
    ADMIN = "admin"


class GroupUser(Base):
    __tablename__ = "group_users"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[GroupRole] = mapped_column(default=GroupRole.MEMBER)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    group: Mapped["Group"] = relationship(back_populates="group_users")
    user: Mapped["User"] = relationship(back_populates="group_users")
