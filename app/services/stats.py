""" raw SQL query rather than ORM here."""

from sqlalchemy import text
from sqlalchemy.orm import Session

TOP_TAGS_LIMIT = 10

TOTALS = text(
    """
    SELECT
        (SELECT COUNT(*)
           FROM bookmarks
          WHERE user_id = :user_id)                     AS total_bookmarks,
        (SELECT COUNT(DISTINCT bt.tag_id)
           FROM bookmark_tags bt
           JOIN bookmarks b ON b.id = bt.bookmark_id
          WHERE b.user_id = :user_id)                   AS total_tags
    """
)

TOP_TAGS = text(
    """
    SELECT t.name AS name, COUNT(*) AS count
      FROM tags t
      JOIN bookmark_tags bt ON bt.tag_id = t.id
      JOIN bookmarks b      ON b.id = bt.bookmark_id
     WHERE b.user_id = :user_id
     GROUP BY t.id, t.name
     -- Name as the tiebreaker, so equal counts come back in a stable order
     -- rather than whatever the query planner happens to produce.
     ORDER BY count DESC, t.name ASC
     LIMIT :limit
    """
)

BOOKMARKS_PER_MONTH = text(
    """
    SELECT strftime('%Y-%m', created_at) AS month, COUNT(*) AS count
      FROM bookmarks
     WHERE user_id = :user_id
     GROUP BY month
     ORDER BY month ASC
    """
)

def bookmark_stats(session: Session, user_id: int) -> dict:
    totals = session.execute(TOTALS, {"user_id": user_id}).mappings().one()

    top_tags = session.execute(
        TOP_TAGS, {"user_id": user_id, "limit": TOP_TAGS_LIMIT}
    ).mappings().all()

    per_month = session.execute(
        BOOKMARKS_PER_MONTH, {"user_id": user_id}
    ).mappings().all()

    return {
        "total_bookmarks": totals["total_bookmarks"],
        "total_tags": totals["total_tags"],
        "top_tags": [dict(row) for row in top_tags],
        "bookmarks_per_month": [dict(row) for row in per_month],
    }
