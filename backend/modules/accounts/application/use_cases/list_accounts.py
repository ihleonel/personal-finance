from __future__ import annotations

from dataclasses import dataclass

from modules.accounts.application.dtos import AccountOutput
from modules.accounts.domain.repositories import AccountRepository
from modules.shared.application.result import Result


@dataclass
class ListAccountsUseCase:
    repository: AccountRepository

    def execute(self, owner_id: int) -> Result[list[AccountOutput]]:
        accounts = self.repository.list_by_owner(owner_id)
        outputs = [
            AccountOutput(
                id=a.id or 0,
                owner_id=a.owner_id,
                name=a.name,
                account_type=a.account_type,
                currency=a.currency,
                initial_balance=str(a.initial_balance),
                is_active=a.is_active,
            )
            for a in accounts
        ]
        return Result.ok(outputs)