from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from modules.shared.application.result import Result
from modules.transactions.domain.repositories import TransactionRepository


@dataclass
class DeleteTransactionUseCase:
    repository: TransactionRepository

    def execute(self, owner_id: int, transaction_id: int) -> Result[bool]:
        result = Result[bool]()

        tx = self.repository.find_by_id(transaction_id)
        if tx is None or tx.owner_id != owner_id:
            result.add_error(
                "non_field_errors",
                "transactions.transaction.not_found",
                str(_("Transacción no encontrada.")),
            )
            return result

        if tx.transfer_group_id is not None:
            self.repository.delete_transfer_group(tx.transfer_group_id)
        else:
            self.repository.delete(transaction_id)

        return Result.ok(True)