from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from modules.auths.application.ports import TokenService


UserModel = get_user_model()


class JWTTokenService(TokenService):
    def __init__(self, user_model=UserModel) -> None:
        self._user_model = user_model

    def generate_tokens(self, user_id: int) -> tuple[str, str]:
        user = self._user_model.objects.get(pk=user_id)
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token), str(refresh)

    def blacklist_refresh(self, refresh: str) -> None:
        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except TokenError as exc:
            raise ValueError("Invalid refresh token.") from exc
