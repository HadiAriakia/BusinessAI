from app.jwt_tokens import decode_access_token
from tests.conftest import REGISTRATION

CREDENTIALS = {"email": REGISTRATION["email"], "password": REGISTRATION["password"]}


def test_login_returns_200_with_a_usable_token(client, registered):
    response = client.post("/auth/login", json=CREDENTIALS)

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["id"] == registered["user"]["id"]
    assert decode_access_token(body["token"]) == registered["user"]["id"]


def test_login_email_is_case_insensitive(client, registered):
    response = client.post(
        "/auth/login", json={**CREDENTIALS, "email": "HUGH@EXAMPLE.COM"}
    )

    assert response.status_code == 200


def test_wrong_password_is_401(client, registered):
    response = client.post("/auth/login", json={**CREDENTIALS, "password": "wrong"})

    assert response.status_code == 401


def test_unknown_email_is_indistinguishable_from_wrong_password(client, registered):
    wrong_password = client.post(
        "/auth/login", json={**CREDENTIALS, "password": "wrong"}
    )
    unknown_email = client.post(
        "/auth/login", json={**CREDENTIALS, "email": "nobody@example.com"}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
