from __future__ import annotations

from django.contrib.auth.hashers import check_password

from modules.auths.application.dtos import (
    AuthTokensOutput,
    LoginInput,
    LoginOutput,
    UserOutput,
)
from modules.auths.application.ports import TokenService
from modules.auths.domain.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from modules.auths.domain.repositories import UserRepository
from modules.auths.domain.value_objects import Email


class LoginUserUseCase:
    def __init__(self, repository: UserRepository, token_service: TokenService) -> None:
        self._repository = repository
        self._token_service = token_service

    def execute(self, data: LoginInput) -> LoginOutput:
        email = Email(data.email)

        user = self._repository.find_by_email(email.value)
        if user is None:
            raise UserNotFoundError(f"No user with email {email.value}.")

        password_hash = self._repository.get_password_hash(email.value)
        if not password_hash or not check_password(data.password, password_hash):
            raise InvalidCredentialsError("Invalid credentials.")

        if not user.is_active:
            raise InactiveUserError("User is inactive.")

        access, refresh = self._token_service.generate_tokens(user.id)

        return LoginOutput(
            user=UserOutput(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
            ),
            tokens=AuthTokensOutput(access=access, refresh=refresh),
        )
