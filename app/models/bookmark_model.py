from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.declarative_base import Base
from app.models.tag_model import bookmark_tags
from app.models.user_model import User
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.tag_model import Tag

class Bookmark(Base):
    __tablename__ = "bookmarks"
    __table_args__ = (

        CheckConstraint(
            "url LIKE 'http://%' OR url LIKE 'https://%'", name="url_scheme"
        ),
        CheckConstraint("length(trim(title)) > 0", name="title_not_blank"),
        Index("ix_bookmarks_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="bookmarks")
    tags: Mapped[list["Tag"]] = relationship(
        secondary=bookmark_tags, back_populates="bookmarks"
    )

    def __repr__(self) -> str:
        return f"<Bookmark id={self.id} title={self.title!r}>"
