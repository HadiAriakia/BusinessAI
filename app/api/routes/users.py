from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models import User
from app.schemas.auth import UserResponse

router = APIRouter(tags=["users"])

@router.get(
    "/me",
    response_model=UserResponse,
    summary="The authenticated user",
    responses={401: {"description": "Missing, expired or invalid token"}},
)
def me(user: User = Depends(get_current_user)):
    """Echoes back whoever the token identifies.

    Useful to a client checking whether its token is still good, 
    """
    return user
