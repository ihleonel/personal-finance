from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from modules.auths.domain.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)

# Map domain exceptions to HTTP responses.
_DOMAIN_ERROR_MAP = {
    UserAlreadyExistsError: (status.HTTP_409_CONFLICT, "user_already_exists"),
    UserNotFoundError: (status.HTTP_404_NOT_FOUND, "user_not_found"),
    InvalidCredentialsError: (status.HTTP_401_UNAUTHORIZED, "invalid_credentials"),
    InactiveUserError: (status.HTTP_403_FORBIDDEN, "inactive_user"),
}


def auths_exception_handler(exc, context):
    """Translates domain and selected application errors into HTTP responses."""

    response = exception_handler(exc, context)
    if response is not None:
        return response

    for exc_type, (http_status, code) in _DOMAIN_ERROR_MAP.items():
        if isinstance(exc, exc_type):
            return Response({"detail": str(exc), "code": code}, status=http_status)

    if isinstance(exc, ValueError) and "token" in str(exc).lower():
        return Response(
            {"detail": str(exc), "code": "invalid_token"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None
