"""Framework-independent Phoenix Core API contracts."""

from dataclasses import dataclass
from typing import Any

from phoenix_core.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    PhoenixError,
    ValidationError,
)


@dataclass(frozen=True)
class ApiResponse:
    """Standard successful API response."""

    data: Any
    request_id: str


@dataclass(frozen=True)
class ApiError:
    """Standard API error response."""

    code: str
    message: str
    request_id: str


_ERROR_CODES = {
    ValidationError: "VALIDATION_ERROR",
    NotFoundError: "NOT_FOUND",
    ConflictError: "CONFLICT",
    AuthenticationError: "AUTHENTICATION_ERROR",
    AuthorizationError: "AUTHORIZATION_ERROR",
}


def error_from_exception(
    exception: Exception,
    *,
    request_id: str,
) -> ApiError:
    """Translate a Core exception into a safe API error contract."""

    if isinstance(exception, PhoenixError):
        code = _ERROR_CODES.get(type(exception), "CORE_ERROR")
        return ApiError(
            code=code,
            message=str(exception),
            request_id=request_id,
        )

    return ApiError(
        code="INTERNAL_ERROR",
        message="An internal error occurred.",
        request_id=request_id,
    )
