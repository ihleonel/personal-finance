from __future__ import annotations

from django.contrib.auth.hashers import check_password
from django.utils.translation import gettext_lazy as _

from modules.auths.application.dtos import (
    AuthTokensOutput,
    LoginInput,
    LoginOutput,
    UserOutput,
)
from modules.auths.application.ports import TokenService
from modules.shared.application.result import Result
from modules.auths.domain.repositories import UserRepository
from modules.auths.domain.value_objects import Email


class LoginUserUseCase:
    def __init__(self, repository: UserRepository, token_service: TokenService) -> None:
        self._repository = repository
        self._token_service = token_service

    def execute(self, data: LoginInput) -> Result[LoginOutput]:
        result = Result[LoginOutput]()

        email = Email.try_parse(data.email)
        if email is None:
            result.add_error(
                "email",
                "auth.email.invalid_format",
                str(_("Ingresa un correo electrónico válido.")),
            )

        if not data.password or not isinstance(data.password, str):
            result.add_error(
                "password",
                "auth.password.required",
                str(_("La contraseña es obligatoria.")),
            )

        if result.has_errors and email is None:
            return result

        assert email is not None  # for type-checkers

        if not result.has_errors:
            user = self._repository.find_by_email(email.value)
            if user is None:
                result.add_error(
                    "email",
                    "auth.email.invalid_credentials",
                    str(_("Credenciales inválidas.")),
                )
                return result

            password_hash = self._repository.get_password_hash(email.value)
            if not password_hash or not check_password(data.password, password_hash):
                result.add_error(
                    "password",
                    "auth.password.invalid_credentials",
                    str(_("Credenciales inválidas.")),
                )
                return result

            if not user.is_active:
                result.add_error(
                    "email",
                    "auth.email.inactive",
                    str(_("La cuenta está inactiva.")),
                )
                return result

            access, refresh = self._token_service.generate_tokens(user.id)

            return Result.ok(
                LoginOutput(
                    user=UserOutput(
                        id=user.id,
                        email=user.email,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        is_active=user.is_active,
                    ),
                    tokens=AuthTokensOutput(access=access, refresh=refresh),
                )
            )

        return result