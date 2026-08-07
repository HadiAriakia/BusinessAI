from datetime import datetime

import pytest
from sqlalchemy import select

from app.models import Bookmark
from tests.conftest import BOOKMARK, register


@pytest.fixture
def seeded(client, auth_header, session_factory):
    """Six bookmarks with known tag counts, spread over three months."""
    plan = [
        (["python", "web"], datetime(2026, 1, 15, 12)),
        (["python"], datetime(2026, 1, 20, 12)),
        (["python", "rust"], datetime(2026, 1, 25, 12)),
        (["rust"], datetime(2026, 2, 10, 12)),
        (["python", "web"], datetime(2026, 2, 14, 12)),
        (["sql"], datetime(2026, 3, 1, 12)),
    ]

    for index, (tags, _) in enumerate(plan):
        client.post(
            "/bookmarks",
            json={**BOOKMARK, "url": f"https://example.com/{index}", "tags": tags},
            headers=auth_header,
        )

    # Backdate through the ORM. Raw SQL would write the datetime without
    # microseconds, which SQLite then compares differently as a string.
    with session_factory() as session:
        bookmarks = session.scalars(select(Bookmark).order_by(Bookmark.id)).all()
        for bookmark, (_, created) in zip(bookmarks, plan):
            bookmark.created_at = created
        session.commit()


def test_totals(client, auth_header, seeded):
    body = client.get("/bookmarks/stats", headers=auth_header).json()

    assert body["total_bookmarks"] == 6
    # Distinct tags used, not total tag rows: python, web, rust, sql.
    assert body["total_tags"] == 4


def test_top_tags_are_counted_and_ordered(client, auth_header, seeded):
    body = client.get("/bookmarks/stats", headers=auth_header).json()

    assert body["top_tags"] == [
        {"name": "python", "count": 4},
        # rust before web: equal counts, broken by name so the order is stable.
        {"name": "rust", "count": 2},
        {"name": "web", "count": 2},
        {"name": "sql", "count": 1},
    ]


def test_bookmarks_per_month_groups_by_calendar_month(client, auth_header, seeded):
    body = client.get("/bookmarks/stats", headers=auth_header).json()

    assert body["bookmarks_per_month"] == [
        {"month": "2026-01", "count": 3},
        {"month": "2026-02", "count": 2},
        {"month": "2026-03", "count": 1},
    ]


def test_stats_are_scoped_to_the_caller(client, auth_header, seeded):
    other = register(client, "intruder")
    client.post("/bookmarks", json={**BOOKMARK, "tags": ["theirs"]}, headers=other)

    mine = client.get("/bookmarks/stats", headers=auth_header).json()
    theirs = client.get("/bookmarks/stats", headers=other).json()

    assert mine["total_bookmarks"] == 6
    assert theirs["total_bookmarks"] == 1
    assert [tag["name"] for tag in theirs["top_tags"]] == ["theirs"]
    # A tag another user created must not appear in my counts.
    assert "theirs" not in [tag["name"] for tag in mine["top_tags"]]


def test_empty_account_returns_zeroes_not_an_error(client, auth_header):
    body = client.get("/bookmarks/stats", headers=auth_header).json()

    assert body == {
        "total_bookmarks": 0,
        "total_tags": 0,
        "top_tags": [],
        "bookmarks_per_month": [],
    }


def test_stats_requires_a_token(client):
    assert client.get("/bookmarks/stats").status_code == 401


def test_stats_route_is_not_shadowed_by_the_id_route(client, auth_header, bookmark):
    # /bookmarks/stats is declared before /bookmarks/{bookmark_id}. Reverse
    # them and "stats" is parsed as an int id, giving 422 instead of stats.
    assert client.get("/bookmarks/stats", headers=auth_header).status_code == 200
    assert client.get(f"/bookmarks/{bookmark['id']}", headers=auth_header).status_code == 200
