from __future__ import annotations

from dataclasses import dataclass

from modules.auths.application.dtos import UserOutput
from modules.auths.domain.exceptions import UserNotFoundError
from modules.auths.domain.repositories import UserRepository


@dataclass
class GetUserProfileUseCase:
    repository: UserRepository

    def execute(self, user_id: int) -> UserOutput:
        user = self.repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found.")

        return UserOutput(
            id=user.id or 0,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
        )