from datetime import datetime, timedelta, timezone
from app.config import Settings
import jwt


def create_access_token(user_id: int, settings: Settings = None) -> str:
    settings = settings or Settings()
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings = None) -> int:
    settings = settings or Settings()

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    subject = payload.get("sub")
    if subject is None:
        raise jwt.InvalidTokenError("token has no subject")

    try:
        return int(subject)
    except ValueError:
        raise jwt.InvalidTokenError("subject is not a user id")
