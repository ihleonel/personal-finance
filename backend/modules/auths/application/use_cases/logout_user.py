from __future__ import annotations

from dataclasses import dataclass

from modules.auths.application.dtos import LogoutInput
from modules.auths.application.ports import TokenService


@dataclass
class LogoutUserUseCase:
    token_service: TokenService

    def execute(self, data: LogoutInput) -> None:
        self.token_service.blacklist_refresh(data.refresh)
