from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from modules.shared.application.result import Result
from modules.transactions.application.dtos import (
    LinkTransferInput,
    TransactionOutput,
    TransferOutput,
)
from modules.transactions.domain.repositories import TransactionRepository
from modules.transactions.models import Transaction as TransactionORM
from modules.transactions.models import new_transfer_group_id


@dataclass
class LinkTransferUseCase:
    repository: TransactionRepository

    def execute(self, data: LinkTransferInput) -> Result[TransferOutput]:
        result = Result[TransferOutput]()

        source = self.repository.find_by_id(data.source_id)
        destination = self.repository.find_by_id(data.destination_id)

        if source is None or destination is None:
            result.add_error(
                "non_field_errors",
                "transactions.transfer.not_found",
                str(_("Una de las transacciones no existe.")),
            )
            return result

        if source.owner_id != data.owner_id or destination.owner_id != data.owner_id:
            result.add_error(
                "non_field_errors",
                "transactions.transfer.not_owned",
                str(_("La transacción no te pertenece.")),
            )
            return result

        if source.transfer_group_id is not None or destination.transfer_group_id is not None:
            result.add_error(
                "non_field_errors",
                "transactions.transfer.already_linked",
                str(_("Esa transacción ya es parte de una transferencia.")),
            )
            return result

        if source.account_id == destination.account_id:
            result.add_error(
                "non_field_errors",
                "transactions.transfer.same_account",
                str(_("La cuenta de origen y destino no pueden ser la misma.")),
            )
            return result

        kinds = {source.kind, destination.kind}
        if kinds != {TransactionORM.Kind.EXPENSE, TransactionORM.Kind.INCOME}:
            result.add_error(
                "non_field_errors",
                "transactions.transfer.invalid_kinds",
                str(_("Debe ser un egreso y un ingreso.")),
            )
            return result

        if abs(source.amount) != abs(destination.amount):
            result.add_error(
                "non_field_errors",
                "transactions.transfer.amount_mismatch",
                str(_("Los montos no coinciden.")),
            )
            return result

        group_id = new_transfer_group_id()
        source_tx, destination_tx = self.repository.link_transfer(
            source_id=data.source_id,
            destination_id=data.destination_id,
            transfer_group_id=group_id,
        )

        return Result.ok(
            TransferOutput(
                source=self._to_output(source_tx),
                destination=self._to_output(destination_tx),
            )
        )

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