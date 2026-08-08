"""The shape every error response takes."""

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


# Codes are machine-readable; clients branch on these, not on the message.
VALIDATION_ERROR = "VALIDATION_ERROR"
UNAUTHENTICATED = "UNAUTHENTICATED"
FORBIDDEN = "FORBIDDEN"
NOT_FOUND = "NOT_FOUND"
CONFLICT = "CONFLICT"
INTERNAL_ERROR = "INTERNAL_ERROR"

# So routes keep raising plain HTTPExceptions and the mapping lives in one place.
STATUS_TO_CODE = {
    400: VALIDATION_ERROR,
    401: UNAUTHENTICATED,
    403: FORBIDDEN,
    404: NOT_FOUND,
    409: CONFLICT,
    422: VALIDATION_ERROR,
}
