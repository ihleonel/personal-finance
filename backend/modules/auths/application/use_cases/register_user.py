from __future__ import annotations

from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _

from modules.auths.application.dtos import (
    AuthTokensOutput,
    RegisterInput,
    RegisterOutput,
    UserOutput,
)
from modules.auths.application.ports import TokenService
from modules.shared.application.result import Result
from modules.auths.domain.repositories import UserRepository
from modules.auths.domain.value_objects import Email


_MIN_PASSWORD_LENGTH = 8


class RegisterUserUseCase:
    def __init__(self, repository: UserRepository, token_service: TokenService) -> None:
        self._repository = repository
        self._token_service = token_service

    def execute(self, data: RegisterInput) -> Result[RegisterOutput]:
        result = Result[RegisterOutput]()

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
        elif len(data.password) < _MIN_PASSWORD_LENGTH:
            result.add_error(
                "password",
                "auth.password.too_short",
                str(_("La contraseña debe tener al menos 8 caracteres.")),
            )

        if email is not None and self._repository.exists_by_email(email.value):
            result.add_error(
                "email",
                "auth.email.already_exists",
                str(_("Este correo ya está registrado.")),
            )

        if result.has_errors:
            return result

        password_hash = make_password(data.password)
        saved = self._repository.save(
            email=email.value,  # type: ignore[union-attr]
            password_hash=password_hash,
            first_name=data.first_name,
            last_name=data.last_name,
        )

        access, refresh = self._token_service.generate_tokens(saved.id)

        return Result.ok(
            RegisterOutput(
                user=UserOutput(
                    id=saved.id,
                    email=saved.email,
                    first_name=saved.first_name,
                    last_name=saved.last_name,
                    is_active=saved.is_active,
                ),
                tokens=AuthTokensOutput(access=access, refresh=refresh),
            )
        )