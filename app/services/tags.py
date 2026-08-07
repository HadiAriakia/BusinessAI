from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Tag


def get_or_create_tags(session: Session, names: list[str]) -> list[Tag]:

    names = list(dict.fromkeys(names))
    if not names:
        return []

    existing = {
        tag.name: tag
        for tag in session.scalars(select(Tag).where(Tag.name.in_(names)))
    }

    tags = []
    for name in names:
        tag = existing.get(name)
        if tag is None:
            tag = Tag(name=name)
            session.add(tag)
            existing[name] = tag
        tags.append(tag)

    session.flush()
    return tags
