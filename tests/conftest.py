import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.main import create_api
from app.dependencies import get_session
from app.models import Base

REGISTRATION = {
    "username": "hugh",
    "email": "hugh@example.com",
    "password": "Password123/",
}


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def client(session_factory):
    api = create_api()

    def override():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    api.dependency_overrides[get_session] = override
    with TestClient(api) as test_client:
        yield test_client


@pytest.fixture
def registered(client):
    """A registered user, with the token from registration."""
    response = client.post("/auth/register", json=REGISTRATION)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def auth_header(registered):
    return {"Authorization": f"Bearer {registered['token']}"}


BOOKMARK = {
    "url": "https://example.com/article",
    "title": "Great Article",
    "description": "An insightful read",
    "tags": ["python", "tutorial"],
}


def register(client, username):
    """Register a second (or third) user and return their auth header."""
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "Password123/",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['token']}"}


@pytest.fixture
def other_header(client, registered):
    """A second user, so ownership scoping can actually be tested."""
    return register(client, "intruder")


@pytest.fixture
def bookmark(client, auth_header):
    response = client.post("/bookmarks", json=BOOKMARK, headers=auth_header)
    assert response.status_code == 201
    return response.json()
