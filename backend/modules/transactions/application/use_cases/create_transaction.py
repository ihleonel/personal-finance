from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional
from uuid import UUID

from django.utils.translation import gettext_lazy as _

from modules.accounts.domain.repositories import AccountRepository
from modules.categories.domain.repositories import CategoryRepository
from modules.shared.application.result import Result
from modules.transactions.application.dtos import (
    CreateTransactionInput,
    TransactionOutput,
)
from modules.transactions.domain.repositories import TransactionRepository
from modules.transactions.domain.value_objects import (
    TransactionAmount,
    TransactionDate,
    TransactionKind,
)


_MAX_DESCRIPTION_LENGTH = 255
_MAX_AMOUNT_DIGITS = 14


@dataclass
class CreateTransactionUseCase:
    repository: TransactionRepository
    account_repository: AccountRepository
    category_repository: Optional[CategoryRepository] = None

    def execute(self, data: CreateTransactionInput) -> Result[TransactionOutput]:
        result = Result[TransactionOutput]()

        kind = TransactionKind.try_parse(data.kind)
        if kind is None:
            result.add_error(
                "kind",
                "transactions.kind.invalid",
                str(_("El tipo de transacción no es válido.")),
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

        account = self.account_repository.find_by_id(data.account_id)
        if account is None or account.owner_id != data.owner_id:
            result.add_error(
                "account",
                "transactions.account.not_found",
                str(_("La cuenta no existe o no te pertenece.")),
            )

        if data.category_id is not None:
            category = None
            if self.category_repository is not None:
                category = self.category_repository.find_by_id(data.category_id)
            if category is None or category.owner_id != data.owner_id:
                result.add_error(
                    "category",
                    "transactions.category.not_found",
                    str(_("La categoría no existe o no te pertenece.")),
                )

        if amount is not None and len(amount.value.as_tuple().digits) > _MAX_AMOUNT_DIGITS:
            result.add_error(
                "amount",
                "transactions.amount.max_digits",
                str(_("El monto no puede tener más de 14 dígitos.")),
            )

        if result.has_errors:
            return result

        saved = self.repository.save(
            owner_id=data.owner_id,
            account_id=data.account_id,
            category_id=data.category_id,
            kind=kind.value if kind is not None else "",  # type: ignore[union-attr]
            amount=amount.value if amount is not None else Decimal("0"),  # type: ignore[union-attr]
            date=parsed_date.value if parsed_date is not None else date.today(),  # type: ignore[union-attr]
            description=data.description,
            transfer_group_id=None,
        )

        return Result.ok(self._to_output(saved))

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