from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from django.utils.translation import gettext_lazy as _

from modules.categories.domain.repositories import CategoryRepository
from modules.shared.application.result import Result
from modules.shared.domain.optional import UNSET
from modules.transactions.application.dtos import (
    TransactionOutput,
    UpdateTransactionInput,
)
from modules.transactions.domain.repositories import TransactionRepository
from modules.transactions.domain.value_objects import (
    TransactionAmount,
    TransactionDate,
)


_MAX_DESCRIPTION_LENGTH = 255
_MAX_AMOUNT_DIGITS = 14


@dataclass
class UpdateTransactionUseCase:
    repository: TransactionRepository
    category_repository: Optional[CategoryRepository] = None

    def execute(
        self,
        owner_id: int,
        transaction_id: int,
        data: UpdateTransactionInput,
    ) -> Result[TransactionOutput]:
        result = Result[TransactionOutput]()

        tx = self.repository.find_by_id(transaction_id)
        if tx is None or tx.owner_id != owner_id:
            result.add_error(
                "non_field_errors",
                "transactions.transaction.not_found",
                str(_("Transacción no encontrada.")),
            )
            return result

        has_any_field = any(
            getattr(data, f) is not None
            for f in ("amount", "date", "description")
        ) or data.is_category_id_set
        if not has_any_field:
            result.add_error(
                "non_field_errors",
                "transactions.transaction.empty_payload",
                str(_("Proporciona al menos un campo para actualizar.")),
            )
            return result

        new_amount: Optional[Decimal] = None
        new_date: Optional[date] = None
        new_description: Optional[str] = None
        new_category_id: Optional[int] = None
        category_provided = False

        if data.amount is not None:
            parsed_amount = TransactionAmount.try_parse(data.amount)
            if parsed_amount is None:
                result.add_error(
                    "amount",
                    "transactions.amount.invalid",
                    str(_("El monto debe ser un número válido mayor a cero.")),
                )
            elif len(parsed_amount.value.as_tuple().digits) > _MAX_AMOUNT_DIGITS:
                result.add_error(
                    "amount",
                    "transactions.amount.max_digits",
                    str(_("El monto no puede tener más de 14 dígitos.")),
                )
            else:
                new_amount = parsed_amount.value

        if data.date is not None:
            parsed_date = TransactionDate.try_parse(data.date)
            if parsed_date is None:
                result.add_error(
                    "date",
                    "transactions.date.invalid",
                    str(_("La fecha no es válida o es posterior a hoy.")),
                )
            else:
                new_date = parsed_date.value

        if data.description is not None:
            if len(data.description) > _MAX_DESCRIPTION_LENGTH:
                result.add_error(
                    "description",
                    "transactions.description.max_length",
                    str(_("La descripción no puede tener más de 255 caracteres.")),
                )
            else:
                new_description = data.description

        if data.is_category_id_set:
            category_provided = True
            new_category_id = data.category_id
            if data.category_id is not None:
                category = None
                if self.category_repository is not None:
                    category = self.category_repository.find_by_id(data.category_id)
                if category is None or category.owner_id != owner_id:
                    result.add_error(
                        "category",
                        "transactions.category.not_found",
                        str(_("La categoría no existe o no te pertenece.")),
                    )

        if result.has_errors:
            return result

        updated = self.repository.update(
            transaction_id=transaction_id,
            amount=new_amount,
            date=new_date,
            description=new_description,
            category_id=new_category_id if category_provided else UNSET,
        )

        return Result.ok(self._to_output(updated))

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
            created_at=tx.created_at.isoformat() if hasattr(tx.created_at, "isoformat") else str(tx.created_at),
        )