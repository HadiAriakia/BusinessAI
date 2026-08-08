# Every error response has the same shape, whatever produced it.

import logging

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.main import create_api
from app.dependencies import get_session
from app.models import User
from tests.conftest import BOOKMARK, REGISTRATION, error_of

VALID_CODES = {
    "VALIDATION_ERROR",
    "UNAUTHENTICATED",
    "FORBIDDEN",
    "NOT_FOUND",
    "CONFLICT",
    "INTERNAL_ERROR",
}


def failures(client, auth_header, other_header, bookmark):
    """One response per error path the API can produce."""
    return {
        401: client.get("/me"),
        403: client.get(f"/bookmarks/{bookmark['id']}", headers=other_header),
        404: client.get("/bookmarks/9999", headers=auth_header),
        409: client.post(
            "/auth/register", json={**REGISTRATION, "email": "other@example.com"}
        ),
        422: client.post(
            "/bookmarks", json={**BOOKMARK, "title": ""}, headers=auth_header
        ),
    }


def test_every_error_uses_the_same_envelope(
    client, auth_header, other_header, bookmark
):
    for status, response in failures(client, auth_header, other_header, bookmark).items():
        assert response.status_code == status
        body = response.json()

        # The whole point: one key, one shape, regardless of what went wrong.
        assert set(body) == {"error"}, f"{status} returned {set(body)}"
        assert set(body["error"]) <= {"code", "message", "details"}
        assert body["error"]["code"] in VALID_CODES
        assert isinstance(body["error"]["message"], str)
        assert body["error"]["message"]


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (401, "UNAUTHENTICATED"),
        (403, "FORBIDDEN"),
        (404, "NOT_FOUND"),
        (409, "CONFLICT"),
        (422, "VALIDATION_ERROR"),
    ],
)
def test_status_maps_to_the_right_code(
    client, auth_header, other_header, bookmark, status, code
):
    response = failures(client, auth_header, other_header, bookmark)[status]

    assert error_of(response)["code"] == code


def test_validation_error_names_the_field_and_constraint(client, auth_header):
    response = client.post(
        "/bookmarks", json={**BOOKMARK, "title": "a" * 201}, headers=auth_header
    )

    error = error_of(response)
    assert error["details"]["field"] == "title"
    assert "title" in error["message"]
    assert error["details"]["constraint"] == "string_too_long"


def test_validation_error_lists_every_failure_not_just_the_first(client, auth_header):
    response = client.post(
        "/bookmarks",
        json={"url": "javascript:alert(1)", "title": ""},
        headers=auth_header,
    )

    fields = {item["field"] for item in error_of(response)["details"]["errors"]}
    assert fields == {"url", "title"}


def test_query_and_path_errors_use_the_envelope_too(client, auth_header):
    bad_query = client.get("/bookmarks", params={"from": "nope"}, headers=auth_header)
    bad_path = client.get("/bookmarks/not-a-number", headers=auth_header)

    assert error_of(bad_query)["details"]["field"] == "from"
    assert error_of(bad_path)["details"]["field"] == "bookmark_id"


def test_401_keeps_its_www_authenticate_header(client):
    response = client.get("/me")

    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_unhandled_exception_returns_the_envelope_and_leaks_nothing(
    session_factory, caplog
):
    api = create_api()

    @api.get("/boom")
    def boom():
        raise ValueError("internal detail: /Users/hugh/secret")

    with TestClient(api, raise_server_exceptions=False) as test_client:
        with caplog.at_level(logging.ERROR):
            response = test_client.get("/boom")

    assert response.status_code == 500
    assert error_of(response)["code"] == "INTERNAL_ERROR"
    # The client learns nothing; the server logs everything.
    assert "internal detail" not in response.text
    assert "Traceback" not in response.text
    assert "internal detail" in caplog.text


def test_database_constraint_violation_becomes_409_not_500(session_factory, caplog):
    """The register race: two signups pass the 'is it taken?' check and the
    unique index catches the loser."""
    api = create_api()

    def override():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    api.dependency_overrides[get_session] = override

    @api.get("/race")
    def race(session: Session = Depends(get_session)):
        session.add(User(username="hugh", email="dup@example.com", password_hash="x"))
        session.commit()

    with TestClient(api, raise_server_exceptions=False) as test_client:
        test_client.post("/auth/register", json=REGISTRATION)
        with caplog.at_level(logging.WARNING):
            response = test_client.get("/race")

    assert response.status_code == 409
    assert error_of(response)["code"] == "CONFLICT"
    # The driver message names tables and columns; that stays server-side.
    assert "users" not in response.text
    assert "UNIQUE" not in response.text


def test_openapi_documents_the_error_schema(client):
    spec = client.get("/openapi.json").json()

    assert "ErrorResponse" in spec["components"]["schemas"]
    assert "ErrorDetail" in spec["components"]["schemas"]
    # The spec must advertise the envelope, or it is lying to clients.
    ref = spec["paths"]["/bookmarks"]["post"]["responses"]["422"]["content"][
        "application/json"
    ]["schema"]["$ref"]
    assert ref.endswith("ErrorResponse")
