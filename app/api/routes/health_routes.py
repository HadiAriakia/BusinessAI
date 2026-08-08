from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.session_dependency import get_session

router = APIRouter(tags=["health"])

@router.get("/health", summary="Liveness and database check")
def health(session: Session = Depends(get_session)) -> dict:
    """Confirms the process is up and the database answers.
    """
    session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
