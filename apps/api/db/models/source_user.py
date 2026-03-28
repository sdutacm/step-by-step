from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class SourceUser(Base):
    __tablename__ = "source_users"
    __table_args__ = (UniqueConstraint("source", "user_id", name="uq_source_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str] = mapped_column(String, index=True)

    user: Mapped["User"] = relationship(back_populates="source_users")
