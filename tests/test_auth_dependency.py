import time
import jwt
import pytest
from app.config import Settings
from app.jwt_tokens import create_access_token


def test_protected_route_with_valid_token(client, auth_header, registered):
    response = client.get("/me", headers=auth_header)

    assert response.status_code == 200
    assert response.json() == registered["user"]


def test_protected_route_without_token_is_401(client):
    response = client.get("/me")

    assert response.status_code == 401
    # RFC 7235 requires this header on a 401.
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    ("label", "header"),
    [
        ("empty", ""),
        ("wrong scheme", "Basic abc"),
        ("no credentials", "Bearer"),
        ("garbage", "Bearer not-a-token"),
    ],
)
def test_malformed_authorization_header_is_401(client, label, header):
    response = client.get("/me", headers={"Authorization": header})

    assert response.status_code == 401


def test_tampered_token_is_401(client, registered):
    tampered = registered["token"][:-4] + "AAAA"

    response = client.get("/me", headers={"Authorization": f"Bearer {tampered}"})

    assert response.status_code == 401


def test_token_signed_with_another_key_is_401(client, registered):
    forged = jwt.encode({"sub": "1"}, "an-attackers-key-that-is-long-enough", algorithm="HS256")

    response = client.get("/me", headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 401


def test_alg_none_forgery_is_401(client, registered):
    forged = jwt.encode({"sub": "1"}, None, algorithm="none")

    response = client.get("/me", headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 401


def test_expired_token_is_401(client, registered, monkeypatch):
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "0")
    expired = create_access_token(registered["user"]["id"], Settings())
    time.sleep(1.1)

    response = client.get("/me", headers={"Authorization": f"Bearer {expired}"})

    assert response.status_code == 401


def test_valid_token_for_a_user_that_does_not_exist_is_401(client):
    # Correctly signed, unexpired, but nobody with that id — a deleted account.
    orphan = create_access_token(9999)

    response = client.get("/me", headers={"Authorization": f"Bearer {orphan}"})

    assert response.status_code == 401


def test_all_rejections_return_the_same_body(client, registered):
    responses = [
        client.get("/me"),
        client.get("/me", headers={"Authorization": "Bearer not-a-token"}),
        client.get("/me", headers={"Authorization": f"Bearer {create_access_token(9999)}"}),
    ]

    bodies = {response.text for response in responses}
    assert len(bodies) == 1, "rejection reason is distinguishable by the client"
