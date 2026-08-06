from fastapi import FastAPI
from app.api.routes import auth, health, users

def create_api() -> FastAPI:
    api = FastAPI(
        title="Bookmarks API",
        description="A personal bookmarks manager.",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    api.include_router(health.router)
    api.include_router(auth.router)
    api.include_router(users.router)

    return api
