from __future__ import annotations

from dataclasses import dataclass

from modules.auths.application.dtos import UserOutput
from modules.auths.domain.entities import User


@dataclass
class GetCurrentUserUseCase:
    def execute(self, user: User) -> UserOutput:
        return UserOutput(
            id=user.id or 0,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
        )
