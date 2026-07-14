from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.utils.translation import gettext_lazy as _

from modules.categories.domain.repositories import CategoryRepository
from modules.shared.application.result import Result
from modules.transactions.application.dtos import (
    AssignCategoryByFiltersOutput,
)
from modules.transactions.domain.repositories import TransactionRepository


@dataclass
class AssignCategoryByFiltersUseCase:
    repository: TransactionRepository
    category_repository: Optional[CategoryRepository] = None

    def execute(self, input_data) -> Result[AssignCategoryByFiltersOutput]:
        result = Result[AssignCategoryByFiltersOutput]()

        category = None
        expected_kind: Optional[str] = None
        if input_data.category_id is not None:
            if self.category_repository is None:
                result.add_error(
                    "category",
                    "transactions.category.not_found",
                    str(_("La categoría no existe o no te pertenece.")),
                )
                return result
            category = self.category_repository.find_by_id(input_data.category_id)
            if category is None or category.owner_id != input_data.owner_id or not category.is_active:
                result.add_error(
                    "category",
                    "transactions.category.not_found",
                    str(_("La categoría no existe o no te pertenece.")),
                )
                return result
            expected_kind = category.kind

        updated_count = self.repository.assign_category_by_filters(
            owner_id=input_data.owner_id,
            filters=input_data.filters,
            category_id=input_data.category_id,
            expected_kind=expected_kind,
        )

        if updated_count == 0:
            result.add_error(
                "non_field_errors",
                "transactions.bulk.no_valid_transactions",
                str(_("No hay transacciones que coincidan con los filtros.")),
            )
            return result

        return Result.ok(AssignCategoryByFiltersOutput(updated_count=updated_count))