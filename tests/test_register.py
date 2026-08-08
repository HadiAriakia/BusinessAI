import pytest
from sqlalchemy import select

from app.models import User
from app.security import verify_password
from tests.conftest import REGISTRATION, error_of, failed_field


def test_register_returns_201_with_user_and_token(client):
    response = client.post("/auth/register", json=REGISTRATION)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"user", "token"}
    assert set(body["user"]) == {"id", "username", "email"}
    assert body["user"]["username"] == "hugh"
    assert body["token"]


def test_password_is_hashed_not_stored(client, session_factory):
    client.post("/auth/register", json=REGISTRATION)

    with session_factory() as session:
        user = session.scalar(select(User))

    # Hashed, not encrypted and not plaintext: the stored value must not be the
    # password, but must still verify against it.
    assert user.password_hash != REGISTRATION["password"]
    assert user.password_hash.startswith("$argon2id$")
    assert verify_password(REGISTRATION["password"], user.password_hash)


def test_password_hash_never_appears_in_response(client, session_factory):
    response = client.post("/auth/register", json=REGISTRATION)

    with session_factory() as session:
        stored = session.scalar(select(User)).password_hash

    assert stored not in response.text
    assert REGISTRATION["password"] not in response.text


def test_duplicate_username_is_409(client, registered):
    response = client.post(
        "/auth/register",
        json={**REGISTRATION, "email": "different@example.com"},
    )

    assert response.status_code == 409
    assert error_of(response)["code"] == "CONFLICT"
    assert "username" in error_of(response)["message"]


def test_duplicate_email_is_409_ignoring_case(client, registered):
    # uq_users_email is byte-comparison, so this only works because the schema
    # lowercases the address before it reaches the database.
    response = client.post(
        "/auth/register",
        json={**REGISTRATION, "username": "someone", "email": "HUGH@EXAMPLE.COM"},
    )

    assert response.status_code == 409
    assert error_of(response)["code"] == "CONFLICT"
    assert "email" in error_of(response)["message"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("email", "not-an-email"),
        ("password", "short"),
        ("username", "ab"),
        ("username", "a" * 81),
    ],
)
def test_invalid_input_is_422_naming_the_field(client, field, value):
    response = client.post("/auth/register", json={**REGISTRATION, field: value})

    assert response.status_code == 422
    assert error_of(response)["code"] == "VALIDATION_ERROR"
    assert failed_field(response) == field


def test_missing_field_is_422(client):
    response = client.post("/auth/register", json={"username": "hugh"})

    assert response.status_code == 422
