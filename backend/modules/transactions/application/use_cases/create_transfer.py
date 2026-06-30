from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.utils.translation import gettext_lazy as _

from modules.accounts.domain.repositories import AccountRepository
from modules.shared.application.result import Result
from modules.transactions.application.dtos import (
    CreateTransferInput,
    TransactionOutput,
    TransferOutput,
)
from modules.transactions.domain.repositories import TransactionRepository
from modules.transactions.domain.value_objects import (
    TransactionAmount,
    TransactionDate,
)


_MAX_AMOUNT_DIGITS = 14
_MAX_DESCRIPTION_LENGTH = 255


@dataclass
class CreateTransferUseCase:
    repository: TransactionRepository
    account_repository: AccountRepository

    def execute(self, data: CreateTransferInput) -> Result[TransferOutput]:
        result = Result[TransferOutput]()

        if data.source_account_id == data.destination_account_id:
            result.add_error(
                "non_field_errors",
                "transactions.transfer.same_account",
                str(_("La cuenta de origen y destino no pueden ser la misma.")),
            )

        amount = TransactionAmount.try_parse(data.amount)
        if amount is None:
            result.add_error(
                "amount",
                "transactions.amount.invalid",
                str(_("El monto debe ser un número válido mayor a cero.")),
            )

        parsed_date = TransactionDate.try_parse(data.date)
        if parsed_date is None:
            result.add_error(
                "date",
                "transactions.date.invalid",
                str(_("La fecha no es válida o es posterior a hoy.")),
            )

        if data.description and len(data.description) > _MAX_DESCRIPTION_LENGTH:
            result.add_error(
                "description",
                "transactions.description.max_length",
                str(_("La descripción no puede tener más de 255 caracteres.")),
            )

        source = self.account_repository.find_by_id(data.source_account_id)
        if source is None or source.owner_id != data.owner_id:
            result.add_error(
                "source_account",
                "transactions.account.not_found",
                str(_("La cuenta de origen no existe o no te pertenece.")),
            )

        destination = self.account_repository.find_by_id(data.destination_account_id)
        if destination is None or destination.owner_id != data.owner_id:
            result.add_error(
                "destination_account",
                "transactions.account.not_found",
                str(_("La cuenta de destino no existe o no te pertenece.")),
            )

        if source is not None and not source.is_active:
            result.add_error(
                "source_account",
                "transactions.account.inactive",
                str(_("La cuenta de origen está inactiva.")),
            )

        if destination is not None and not destination.is_active:
            result.add_error(
                "destination_account",
                "transactions.account.inactive",
                str(_("La cuenta de destino está inactiva.")),
            )

        if amount is not None and len(amount.value.as_tuple().digits) > _MAX_AMOUNT_DIGITS:
            result.add_error(
                "amount",
                "transactions.amount.max_digits",
                str(_("El monto no puede tener más de 14 dígitos.")),
            )

        if result.has_errors:
            return result

        source_tx, destination_tx = self.repository.create_transfer(
            owner_id=data.owner_id,
            source_account_id=data.source_account_id,
            destination_account_id=data.destination_account_id,
            amount=amount.value if amount is not None else Decimal("0"),  # type: ignore[union-attr]
            date=parsed_date.value if parsed_date is not None else date.today(),  # type: ignore[union-attr]
            description=data.description,
            category_id=data.category_id,
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