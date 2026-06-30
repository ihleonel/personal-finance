from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from modules.accounts.application.dtos import AccountOutput
from modules.accounts.domain.repositories import AccountRepository
from modules.shared.application.result import Result


@dataclass
class ActivateAccountUseCase:
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

        if account.is_active:
            result.add_error(
                "non_field_errors",
                "accounts.account.already_active",
                str(_("La cuenta ya está activa.")),
            )
            return result

        activated = self.repository.activate(account_id)
        return Result.ok(
            AccountOutput(
                id=activated.id or 0,
                owner_id=activated.owner_id,
                name=activated.name,
                account_type=activated.account_type,
                currency=activated.currency,
                initial_balance=str(activated.initial_balance),
                is_active=activated.is_active,
            )
        )