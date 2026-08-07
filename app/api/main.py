from fastapi import FastAPI
from app.api.routes import auth, bookmarks, health, users

DESCRIPTION = """
A personal bookmarks manager.

**Getting started in this page:**

1. `POST /auth/register` to create an account — the response contains a token.
2. Click **Authorize** at the top right and paste the token.
3. Every `/bookmarks` call is now scoped to that account.
"""

TAGS = [
    {"name": "auth", "description": "Registration and login. No token required."},
    {"name": "bookmarks", "description": "CRUD, scoped to the authenticated user."},
    {"name": "users", "description": "The authenticated account."},
    {"name": "health", "description": "Liveness and database check."},
]


def create_api() -> FastAPI:
    api = FastAPI(
        title="Bookmarks API",
        description=DESCRIPTION,
        version="0.1.0",
        openapi_tags=TAGS,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        swagger_ui_parameters={
            "persistAuthorization": True,
            "defaultModelsExpandDepth": 2,
            "docExpansion": "list",
            "displayRequestDuration": True,
            "tryItOutEnabled": True,
        },
    )

    api.include_router(health.router)
    api.include_router(auth.router)
    api.include_router(users.router)
    api.include_router(bookmarks.router)

    return api
