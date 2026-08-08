from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.session_dependency import get_session
from app.models import User
from app.schemas.auth_schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.password_hashing import hash_password, verify_password
from app.jwt_tokens import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account and receive a token",
    responses={409: {"description": "Username or email already taken"}},
)
def register(payload: RegisterRequest, session: Session = Depends(get_session)):
    taken = session.scalar(
        select(User).where(
            (User.username == payload.username) | (User.email == payload.email)
        )
    )
    if taken is not None:
        field = "username" if taken.username == payload.username else "email"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"That {field} is already registered",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    session.commit()

    return AuthResponse(
        user=UserResponse.model_validate(user),
        token=create_access_token(user.id),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Exchange credentials for a token",
    responses={401: {"description": "Invalid credentials"}},
)
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = session.scalar(select(User).where(User.email == payload.email))

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        token=create_access_token(user.id),
    )
