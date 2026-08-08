import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.session_dependency import get_session
from app.models import User
from app.jwt_tokens import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False, description="JWT from /auth/login")

UNAUTHORISED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise UNAUTHORISED

    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise UNAUTHORISED

    user = session.get(User, user_id)
    if user is None:
        raise UNAUTHORISED

    return user
