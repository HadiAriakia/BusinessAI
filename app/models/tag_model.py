from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.models.declarative_base import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.bookmark_model import Bookmark

# The many-to-many join between bookmarks and tags:

bookmark_tags = Table(
    "bookmark_tags",
    Base.metadata,
    Column(
        "bookmark_id",
        Integer,
        ForeignKey("bookmarks.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        Integer,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),

    Index("ix_bookmark_tags_tag_id", "tag_id"),
)


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        # The spec says lowercase, 
        CheckConstraint("name = lower(name)", name="name_lowercase"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        secondary=bookmark_tags, back_populates="tags"
    )

    @validates("name")
    def normalise_name(self, key: str, value: str) -> str:
        return value.strip().lower()

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name!r}>"
