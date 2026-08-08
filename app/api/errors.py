"""Global exception handlers.

Registered once on the app, so routes keep raising plain HTTPException and no
handler formats its own error body.
"""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.schemas import errors

logger = logging.getLogger(__name__)


def error_response(status_code, code, message, details=None, headers=None):
    body = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body, headers=headers)


def register_error_handlers(api: FastAPI) -> None:
    @api.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        problems = exc.errors()
        # loc is like ("body", "title"); the last part is the field name.
        field = lambda e: str(e["loc"][-1]) if e["loc"] else None
        first = problems[0]

        return error_response(
            422,
            errors.VALIDATION_ERROR,
            # Pydantic's msg omits the field name, so prefix it.
            f"{field(first)}: {first['msg']}",
            {
                "field": field(first),
                "constraint": first["type"],
                # All of them, for a form that highlights every bad input.
                "errors": [
                    {"field": field(e), "message": e["msg"], "constraint": e["type"]}
                    for e in problems
                ],
            },
        )

    @api.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return error_response(
            exc.status_code,
            errors.STATUS_TO_CODE.get(exc.status_code, errors.INTERNAL_ERROR),
            str(exc.detail),
            # Keeps WWW-Authenticate on a 401, which RFC 7235 requires.
            headers=exc.headers,
        )

    @api.exception_handler(IntegrityError)
    async def integrity_error(request: Request, exc: IntegrityError):
        # Mostly the register race: two signups pass the "is it taken?" check
        # and the unique index catches the loser. Without this it is a 500.
        logger.warning("IntegrityError: %s", exc.orig)
        # Vague on purpose — the driver message names tables and columns.
        return error_response(
            409, errors.CONFLICT, "That value conflicts with an existing record"
        )

    @api.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception):
        # Logged in full server-side; the client gets nothing, because stack
        # traces leak file paths and query fragments.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return error_response(
            500, errors.INTERNAL_ERROR, "An unexpected error occurred"
        )
