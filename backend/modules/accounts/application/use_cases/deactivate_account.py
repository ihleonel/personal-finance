from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from modules.accounts.application.dtos import AccountOutput
from modules.accounts.domain.repositories import AccountRepository
from modules.shared.application.result import Result


@dataclass
class DeactivateAccountUseCase:
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

        if not account.is_active:
            result.add_error(
                "non_field_errors",
                "accounts.account.already_inactive",
                str(_("La cuenta ya está inactiva.")),
            )
            return result

        deactivated = self.repository.deactivate(account_id)
        return Result.ok(
            AccountOutput(
                id=deactivated.id or 0,
                owner_id=deactivated.owner_id,
                name=deactivated.name,
                account_type=deactivated.account_type,
                currency=deactivated.currency,
                initial_balance=str(deactivated.initial_balance),
                is_active=deactivated.is_active,
            )
        )