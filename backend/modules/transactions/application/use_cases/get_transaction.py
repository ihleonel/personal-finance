from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from modules.shared.application.result import Result
from modules.transactions.application.dtos import TransactionOutput
from modules.transactions.domain.repositories import TransactionRepository


@dataclass
class GetTransactionUseCase:
    repository: TransactionRepository

    def execute(self, owner_id: int, transaction_id: int) -> Result[TransactionOutput]:
        result = Result[TransactionOutput]()

        tx = self.repository.find_by_id(transaction_id)
        if tx is None or tx.owner_id != owner_id:
            result.add_error(
                "non_field_errors",
                "transactions.transaction.not_found",
                str(_("Transacción no encontrada.")),
            )
            return result

        return Result.ok(self._to_output(tx))

    @staticmethod
    def _to_output(tx) -> TransactionOutput:
        return TransactionOutput(
            id=tx.id or 0,
            owner_id=tx.owner_id,
            account_id=tx.account_id,
            category_id=tx.category_id,
            kind=tx.kind,
            amount=str(tx.amount),
            date=tx.date.isoformat() if hasattr(tx.date, "isoformat") else str(tx.date),
            description=tx.description,
            transfer_group_id=str(tx.transfer_group_id) if tx.transfer_group_id is not None else None,
            created_at=tx.created_at.isoformat() if hasattr(tx.created_at, "isoformat") else str(tx.created_at),
        )