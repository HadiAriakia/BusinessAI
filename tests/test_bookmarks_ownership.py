import pytest
from tests.conftest import BOOKMARK

def test_list_only_shows_your_own(client, auth_header, other_header):
    client.post("/bookmarks", json={**BOOKMARK, "title": "Mine"}, headers=auth_header)
    client.post(
        "/bookmarks",
        json={**BOOKMARK, "url": "https://other.com/", "title": "Theirs"},
        headers=other_header,
    )

    mine = client.get("/bookmarks", headers=auth_header).json()
    theirs = client.get("/bookmarks", headers=other_header).json()

    assert [item["title"] for item in mine] == ["Mine"]
    assert [item["title"] for item in theirs] == ["Theirs"]


def test_a_new_user_sees_an_empty_list(client, auth_header, other_header, bookmark):
    assert client.get("/bookmarks", headers=other_header).json() == []


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_another_users_bookmark_is_403(client, other_header, bookmark, method):
    call = getattr(client, method)
    kwargs = {"json": {"title": "hacked"}} if method == "patch" else {}

    response = call(f"/bookmarks/{bookmark['id']}", headers=other_header, **kwargs)

    assert response.status_code == 403


def test_a_forbidden_patch_does_not_modify_anything(client, auth_header, other_header, bookmark):
    client.patch(
        f"/bookmarks/{bookmark['id']}", json={"title": "hacked"}, headers=other_header
    )

    # The 403 above is only meaningful if the write genuinely did not happen.
    still_there = client.get(f"/bookmarks/{bookmark['id']}", headers=auth_header).json()
    assert still_there["title"] == bookmark["title"]


def test_a_forbidden_delete_does_not_remove_anything(client, auth_header, other_header, bookmark):
    client.delete(f"/bookmarks/{bookmark['id']}", headers=other_header)

    assert client.get(f"/bookmarks/{bookmark['id']}", headers=auth_header).status_code == 200


def test_user_id_in_the_body_cannot_reassign_ownership(client, auth_header, other_header):
    # The owner comes from the token, never the payload.
    created = client.post(
        "/bookmarks", json={**BOOKMARK, "user_id": 9999}, headers=auth_header
    )

    assert created.status_code == 201
    assert client.get("/bookmarks", headers=auth_header).json() != []
    assert client.get("/bookmarks", headers=other_header).json() == []


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/bookmarks"),
        ("get", "/bookmarks"),
        ("get", "/bookmarks/1"),
        ("patch", "/bookmarks/1"),
        ("delete", "/bookmarks/1"),
    ],
)
def test_every_bookmark_route_requires_a_token(client, method, path):
    # httpx's get and delete take no json argument.
    kwargs = {"json": {}} if method in {"post", "patch"} else {}

    response = getattr(client, method)(path, **kwargs)

    assert response.status_code == 401
