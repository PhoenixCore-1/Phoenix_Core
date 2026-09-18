"""Core application/domain errors."""

class PhoenixError(Exception):
    """Base exception for expected Phoenix errors."""

class ValidationError(PhoenixError):
    pass

class NotFoundError(PhoenixError):
    pass

class ConflictError(PhoenixError):
    pass

class AuthenticationError(PhoenixError):
    pass

class AuthorizationError(PhoenixError):
    pass
