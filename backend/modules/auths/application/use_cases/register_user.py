from __future__ import annotations

from django.contrib.auth.hashers import make_password

from modules.auths.application.dtos import RegisterInput, RegisterOutput
from modules.auths.application.ports import TokenService
from modules.auths.domain.exceptions import UserAlreadyExistsError
from modules.auths.domain.repositories import UserRepository
from modules.auths.domain.value_objects import Email


class RegisterUserUseCase:
    def __init__(self, repository: UserRepository, token_service: TokenService) -> None:
        self._repository = repository
        self._token_service = token_service

    def execute(self, data: RegisterInput) -> RegisterOutput:
        email = Email(data.email)

        if self._repository.exists_by_email(email.value):
            raise UserAlreadyExistsError(f"User with email {email.value} already exists.")

        password_hash = make_password(data.password)
        saved = self._repository.save(
            email=email.value,
            password_hash=password_hash,
            first_name=data.first_name,
            last_name=data.last_name,
        )

        access, refresh = self._token_service.generate_tokens(saved.id)

        from modules.auths.application.dtos import AuthTokensOutput, UserOutput

        return RegisterOutput(
            user=UserOutput(
                id=saved.id,
                email=saved.email,
                first_name=saved.first_name,
                last_name=saved.last_name,
                is_active=saved.is_active,
            ),
            tokens=AuthTokensOutput(access=access, refresh=refresh),
        )
