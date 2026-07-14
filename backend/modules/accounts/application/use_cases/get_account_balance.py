from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.utils.translation import gettext_lazy as _

from modules.accounts.application.dtos import AccountBalanceOutput
from modules.accounts.domain.repositories import AccountRepository
from modules.shared.application.result import Result
from modules.transactions.domain.repositories import TransactionRepository


@dataclass
class GetAccountBalanceUseCase:
    repository: TransactionRepository
    account_repository: AccountRepository

    def execute(
        self,
        owner_id: int,
        account_id: int,
        date_to: date | None = None,
    ) -> Result[AccountBalanceOutput]:
        result = Result[AccountBalanceOutput]()

        account = self.account_repository.find_by_id(account_id)
        if account is None or account.owner_id != owner_id:
            result.add_error(
                "non_field_errors",
                "accounts.account.not_found",
                str(_("Cuenta no encontrada.")),
            )
            return result

        txs = self.repository.list_by_owner(
            owner_id=owner_id,
            account_id=account_id,
            date_to=date_to,
        )

        signed_sum = Decimal("0.00")
        for tx in txs:
            signed_sum += tx.amount if tx.kind == "income" else -tx.amount

        current_balance = account.initial_balance + signed_sum

        return Result.ok(
            AccountBalanceOutput(
                account_id=account_id,
                initial_balance=str(account.initial_balance),
                current_balance=str(current_balance.quantize(Decimal("0.01"))),
                as_of=date_to.isoformat() if date_to is not None else None,
            )
        )