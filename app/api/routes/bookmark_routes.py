from datetime import date, datetime, time
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.api.auth_dependency import get_current_user
from app.session_dependency import get_session
from app.models import Bookmark, Tag, User
from app.schemas.bookmark_schemas import BookmarkCreate, BookmarkResponse, BookmarkUpdate
from app.schemas.stats_schemas import StatsResponse
from app.services.stats_queries import bookmark_stats
from app.services.tag_service import get_or_create_tags

router = APIRouter(
    prefix="/bookmarks",
    tags=["bookmarks"],
    responses={401: {"description": "Missing, expired or invalid token"}},
)


@router.post(
    "",
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a bookmark",
)
def create_bookmark(
    payload: BookmarkCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    bookmark = Bookmark(
        url=str(payload.url),
        title=payload.title,
        description=payload.description,
        user_id=user.id,
        tags=get_or_create_tags(session, payload.tags),
    )

    session.add(bookmark)
    session.commit()

    return bookmark


@router.get(
    "",
    response_model=list[BookmarkResponse],
    summary="List your bookmarks",
)
def list_bookmarks(
    tag: str | None = Query(
        default=None,
        description="Only bookmarks carrying this tag. Case-insensitive.",
        examples=["python"],
    ),
    q: str | None = Query(
        default=None,
        description="Case-insensitive substring of the title or description.",
        examples=["fastapi"],
    ),
    date_from: date | None = Query(
        default=None,
        alias="from",
        description="Created on or after this date (inclusive).",
    ),
    date_to: date | None = Query(
        default=None,
        alias="to",
        description="Created on or before this date (inclusive).",
    ),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Newest first. Only the authenticated user's bookmarks, ever.

    Filters combine with AND: `?tag=python&q=async` means both.
    """
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=422, detail="'from' must not be after 'to'"
        )

    statement = (
        select(Bookmark)
        .where(Bookmark.user_id == user.id)
        .options(selectinload(Bookmark.tags))
        .order_by(Bookmark.created_at.desc(), Bookmark.id.desc())
    )

    if tag:
        statement = statement.join(Bookmark.tags).where(Tag.name == tag.strip().lower())

    if q:
        pattern = f"%{q.strip()}%"
        statement = statement.where(
            Bookmark.title.ilike(pattern) | Bookmark.description.ilike(pattern)
        )

    if date_from:
        statement = statement.where(
            Bookmark.created_at >= datetime.combine(date_from, time.min)
        )

    if date_to:
        # time.max makes "to" inclusive of the whole day.
        statement = statement.where(
            Bookmark.created_at <= datetime.combine(date_to, time.max)
        )

    return session.scalars(statement).all()


# Declared before /{bookmark_id}. FastAPI matches routes in registration
# order, so with the reverse order "stats" would be tried as a bookmark_id and
# come back 422 instead of reaching this handler.
@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Aggregate counts over your bookmarks",
)
def stats(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Totals, most-used tags, and bookmarks per month.

    Implemented in raw SQL rather than the ORM — see app/services/stats.py.
    """
    return bookmark_stats(session, user.id)


@router.get(
    "/{bookmark_id}",
    response_model=BookmarkResponse,
    summary="Get one bookmark",
    responses={
        403: {"description": "The bookmark belongs to another user"},
        404: {"description": "No bookmark with that id"},
    },
)
def get_bookmark(
    bookmark_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return load_owned_bookmark(session, bookmark_id, user)


@router.patch(
    "/{bookmark_id}",
    response_model=BookmarkResponse,
    summary="Update a bookmark",
    responses={
        403: {"description": "The bookmark belongs to another user"},
        404: {"description": "No bookmark with that id"},
    },
)
def update_bookmark(
    bookmark_id: int,
    payload: BookmarkUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """PATCH, so omitted fields are left alone.

    An explicit `"description": null` clears it; omitting the key does not.
    """
    bookmark = load_owned_bookmark(session, bookmark_id, user)

    changes = payload.model_dump(exclude_unset=True)

    if "tags" in changes:
        bookmark.tags = get_or_create_tags(session, changes.pop("tags") or [])

    if "url" in changes and changes["url"] is not None:
        changes["url"] = str(changes["url"])

    for field, value in changes.items():
        setattr(bookmark, field, value)

    session.commit()

    return bookmark


@router.delete(
    "/{bookmark_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bookmark",
    responses={
        204: {"description": "Deleted"},
        403: {"description": "The bookmark belongs to another user"},
        404: {"description": "No bookmark with that id"},
    },
)
def delete_bookmark(
    bookmark_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    bookmark = load_owned_bookmark(session, bookmark_id, user)
    session.delete(bookmark)
    session.commit()

    return None


def load_owned_bookmark(session: Session, bookmark_id: int, user: User) -> Bookmark:

    bookmark = session.scalar(
        select(Bookmark)
        .where(Bookmark.id == bookmark_id)
        .options(selectinload(Bookmark.tags))
    )

    if bookmark is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found"
        )

    if bookmark.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This bookmark belongs to another user",
        )

    return bookmark