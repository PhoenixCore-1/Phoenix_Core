from phoenix_core.api.contracts import (
    ApiError,
    ApiResponse,
    error_from_exception,
)
from phoenix_core.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)


def test_api_response_contains_data_and_request_id():
    response = ApiResponse(
        data={"status": "ok"},
        request_id="req-001",
    )

    assert response.data == {"status": "ok"}
    assert response.request_id == "req-001"


def test_validation_error_maps_to_stable_api_code():
    error = error_from_exception(
        ValidationError("Invalid input."),
        request_id="req-002",
    )

    assert error == ApiError(
        code="VALIDATION_ERROR",
        message="Invalid input.",
        request_id="req-002",
    )


def test_not_found_error_maps_to_stable_api_code():
    error = error_from_exception(
        NotFoundError("Document not found."),
        request_id="req-003",
    )

    assert error.code == "NOT_FOUND"
    assert error.message == "Document not found."
    assert error.request_id == "req-003"


def test_conflict_error_maps_to_stable_api_code():
    error = error_from_exception(
        ConflictError("Already exists."),
        request_id="req-004",
    )

    assert error.code == "CONFLICT"


def test_authentication_error_maps_to_stable_api_code():
    error = error_from_exception(
        AuthenticationError("Authentication required."),
        request_id="req-005",
    )

    assert error.code == "AUTHENTICATION_ERROR"


def test_authorization_error_maps_to_stable_api_code():
    error = error_from_exception(
        AuthorizationError("Access denied."),
        request_id="req-006",
    )

    assert error.code == "AUTHORIZATION_ERROR"


def test_unexpected_exception_is_safe():
    error = error_from_exception(
        RuntimeError("database password leaked"),
        request_id="req-007",
    )

    assert error.code == "INTERNAL_ERROR"
    assert error.message == "An internal error occurred."
    assert "database password" not in error.message
