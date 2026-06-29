"""
app/core/exceptions.py
──────────────────────
Centralised exception hierarchy.
All exceptions map to specific HTTP status codes and structured error bodies.
Handlers are registered in main.py so every exception returns the same JSON shape:
  {"detail": "...", "error_code": "..."}
"""

from fastapi import HTTPException, status


class CineAIException(HTTPException):
    """Base exception — all app exceptions inherit from this."""
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str, status_code: int = 500):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(CineAIException):
    error_code = "NOT_FOUND"

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedException(CineAIException):
    error_code = "UNAUTHORIZED"

    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(CineAIException):
    error_code = "FORBIDDEN"

    def __init__(self, detail: str = "Access denied"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class ConflictException(CineAIException):
    error_code = "CONFLICT"

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class BadRequestException(CineAIException):
    error_code = "BAD_REQUEST"

    def __init__(self, detail: str = "Invalid request"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class ServiceUnavailableException(CineAIException):
    error_code = "SERVICE_UNAVAILABLE"

    def __init__(self, detail: str = "External service unavailable"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
