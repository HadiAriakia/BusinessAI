import pytest

from tests.conftest import BOOKMARK, error_of, failed_field


def test_create_returns_201_with_the_full_resource(client, auth_header):
    response = client.post("/bookmarks", json=BOOKMARK, headers=auth_header)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Great Article"
    assert body["description"] == "An insightful read"
    assert body["tags"] == ["python", "tutorial"]
    assert body["id"] and body["created_at"] and body["updated_at"]


def test_create_normalises_the_url(client, auth_header):
    response = client.post(
        "/bookmarks", json={**BOOKMARK, "url": "https://example.com"}, headers=auth_header
    )

    # Pydantic's HttpUrl appends the empty path, so the same site cannot be
    # stored two ways.
    assert response.json()["url"] == "https://example.com/"


def test_create_deduplicates_and_lowercases_tags(client, auth_header):
    response = client.post(
        "/bookmarks",
        json={**BOOKMARK, "tags": ["Python", "python", " PYTHON ", "Rust"]},
        headers=auth_header,
    )

    assert response.json()["tags"] == ["python", "rust"]


def test_tags_are_shared_between_bookmarks(client, auth_header):
    first = client.post("/bookmarks", json={**BOOKMARK, "tags": ["python"]}, headers=auth_header)
    second = client.post(
        "/bookmarks",
        json={**BOOKMARK, "url": "https://example.com/b", "tags": ["python", "rust"]},
        headers=auth_header,
    )

    # Both report the tag; the point is that the second call reuses the row
    # rather than tripping uq_tags_name.
    assert "python" in first.json()["tags"]
    assert second.status_code == 201
    assert second.json()["tags"] == ["python", "rust"]


def test_list_returns_newest_first(client, auth_header):
    for index in range(3):
        client.post(
            "/bookmarks",
            json={**BOOKMARK, "url": f"https://example.com/{index}", "title": f"Number {index}"},
            headers=auth_header,
        )

    titles = [item["title"] for item in client.get("/bookmarks", headers=auth_header).json()]

    assert titles == ["Number 2", "Number 1", "Number 0"]


def test_get_one_returns_the_bookmark(client, auth_header, bookmark):
    response = client.get(f"/bookmarks/{bookmark['id']}", headers=auth_header)

    assert response.status_code == 200
    assert response.json() == bookmark


def test_get_unknown_id_is_404(client, auth_header):
    assert client.get("/bookmarks/9999", headers=auth_header).status_code == 404


def test_patch_only_touches_the_fields_sent(client, auth_header, bookmark):
    response = client.patch(
        f"/bookmarks/{bookmark['id']}", json={"title": "Renamed"}, headers=auth_header
    )

    body = response.json()
    assert body["title"] == "Renamed"
    # The classic PATCH bug: a partial update wiping everything else.
    assert body["description"] == bookmark["description"]
    assert body["tags"] == bookmark["tags"]
    assert body["url"] == bookmark["url"]


def test_patch_with_explicit_null_clears_the_field(client, auth_header, bookmark):
    response = client.patch(
        f"/bookmarks/{bookmark['id']}", json={"description": None}, headers=auth_header
    )

    # Distinguishable from omitting the key, which is what exclude_unset buys.
    assert response.json()["description"] is None


def test_patch_replaces_tags_rather_than_appending(client, auth_header, bookmark):
    response = client.patch(
        f"/bookmarks/{bookmark['id']}", json={"tags": ["rust"]}, headers=auth_header
    )

    assert response.json()["tags"] == ["rust"]


def test_patch_moves_updated_at_but_not_created_at(client, auth_header, bookmark):
    response = client.patch(
        f"/bookmarks/{bookmark['id']}", json={"title": "Renamed"}, headers=auth_header
    )

    body = response.json()
    assert body["updated_at"] > bookmark["updated_at"]
    assert body["created_at"] == bookmark["created_at"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("url", "javascript:alert(1)"),
        ("url", "ftp://example.com"),
        ("title", "   "),
        ("title", "a" * 201),
        ("description", "a" * 501),
    ],
)
def test_invalid_input_is_422(client, auth_header, field, value):
    response = client.post(
        "/bookmarks", json={**BOOKMARK, field: value}, headers=auth_header
    )

    assert response.status_code == 422
    assert error_of(response)["code"] == "VALIDATION_ERROR"
    assert failed_field(response) == field


def test_patch_is_validated_too(client, auth_header, bookmark):
    # A PATCH must not be a way around the rules that apply on create.
    response = client.patch(
        f"/bookmarks/{bookmark['id']}", json={"url": "javascript:alert(1)"}, headers=auth_header
    )

    assert response.status_code == 422


def test_delete_returns_204_with_no_body(client, auth_header, bookmark):
    response = client.delete(f"/bookmarks/{bookmark['id']}", headers=auth_header)

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/bookmarks/{bookmark['id']}", headers=auth_header).status_code == 404


def test_deleting_a_bookmark_keeps_the_tags(client, auth_header, bookmark):
    client.delete(f"/bookmarks/{bookmark['id']}", headers=auth_header)

    # Tags are global; another user's bookmark may still need "python".
    response = client.post("/bookmarks", json=BOOKMARK, headers=auth_header)
    assert response.json()["tags"] == ["python", "tutorial"]
