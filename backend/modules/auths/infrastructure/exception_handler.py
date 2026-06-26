from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def auths_exception_handler(exc, context):
    """Translates non-domain exceptions into HTTP responses.

    Domain validation errors are returned via Result objects, so this handler
    only deals with infrastructure-level failures (e.g. invalid JWT refresh
    token during logout) and delegates the rest to DRF's default handler.
    """

    response = exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, ValueError) and "token" in str(exc).lower():
        return Response(
            {"detail": str(_("Token de actualización inválido.")), "code": "auth.token.invalid"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None