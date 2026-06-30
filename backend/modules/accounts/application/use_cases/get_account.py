from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from modules.accounts.application.dtos import AccountOutput
from modules.accounts.domain.repositories import AccountRepository
from modules.shared.application.result import Result


@dataclass
class GetAccountUseCase:
    repository: AccountRepository

    def execute(self, owner_id: int, account_id: int) -> Result[AccountOutput]:
        result = Result[AccountOutput]()

        account = self.repository.find_by_id(account_id)
        if account is None or account.owner_id != owner_id:
            result.add_error(
                "non_field_errors",
                "accounts.account.not_found",
                str(_("Cuenta no encontrada.")),
            )
            return result

        return Result.ok(
            AccountOutput(
                id=account.id or 0,
                owner_id=account.owner_id,
                name=account.name,
                account_type=account.account_type,
                currency=account.currency,
                initial_balance=str(account.initial_balance),
                is_active=account.is_active,
            )
        )