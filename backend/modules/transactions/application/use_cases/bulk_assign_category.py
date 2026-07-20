from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.utils.translation import gettext_lazy as _

from modules.categories.domain.repositories import CategoryRepository
from modules.shared.application.result import Result
from modules.transactions.application.dtos import (
    BulkAssignCategoryInput,
    BulkAssignCategoryOutput,
)
from modules.transactions.domain.repositories import TransactionRepository


@dataclass
class BulkAssignCategoryUseCase:
    repository: TransactionRepository
    category_repository: Optional[CategoryRepository] = None

    def execute(self, data: BulkAssignCategoryInput) -> Result[BulkAssignCategoryOutput]:
        result = Result[BulkAssignCategoryOutput]()

        if not data.transaction_ids:
            result.add_error(
                "transaction_ids",
                "transactions.bulk.empty",
                str(_("Seleccioná al menos una transacción.")),
            )
            return result

        category = None
        expected_kind: Optional[str] = None
        if data.category_id is not None:
            if self.category_repository is None:
                result.add_error(
                    "category",
                    "transactions.category.not_found",
                    str(_("La categoría no existe o no te pertenece.")),
                )
                return result
            category = self.category_repository.find_by_id(data.category_id)
            if category is None or category.owner_id != data.owner_id or not category.is_active:
                result.add_error(
                    "category",
                    "transactions.category.not_found",
                    str(_("La categoría no existe o no te pertenece.")),
                )
                return result
            expected_kind = category.kind

        bulk = self.repository.bulk_assign_category(
            owner_id=data.owner_id,
            transaction_ids=list(data.transaction_ids),
            category_id=data.category_id,
            expected_kind=expected_kind,
        )

        if bulk.updated_count == 0:
            if bulk.skipped_kinds:
                result.add_error(
                    "non_field_errors",
                    "transactions.bulk.kind_mismatch",
                    str(
                        _(
                            "Ninguna transacción coincide con el tipo de la categoría. "
                            "Filtrá por tipo antes de asignar."
                        )
                    ),
                )
            else:
                result.add_error(
                    "non_field_errors",
                    "transactions.bulk.no_valid_transactions",
                    str(_("No hay transacciones válidas para actualizar.")),
                )
            return result

        return Result.ok(
            BulkAssignCategoryOutput(
                updated_count=bulk.updated_count,
                skipped_ids=bulk.skipped_ids,
                skipped_kinds=bulk.skipped_kinds,
            )
        )