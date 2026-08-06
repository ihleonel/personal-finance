from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from modules.categories.application.dtos import CategoryOutput
from modules.categories.domain.repositories import CategoryRepository
from modules.shared.application.result import Result


@dataclass
class DeactivateCategoryUseCase:
    repository: CategoryRepository

    def execute(self, owner_id: int, category_id: int) -> Result[CategoryOutput]:
        result = Result[CategoryOutput]()

        category = self.repository.find_by_id(category_id)
        if category is None or category.owner_id != owner_id:
            result.add_error(
                "non_field_errors",
                "categories.category.not_found",
                str(_("Categoría no encontrada.")),
            )
            return result

        if not category.is_active:
            result.add_error(
                "non_field_errors",
                "categories.category.already_inactive",
                str(_("La categoría ya está inactiva.")),
            )
            return result

        deactivated = self.repository.deactivate(category_id)
        return Result.ok(
            CategoryOutput(
                id=deactivated.id or 0,
                owner_id=deactivated.owner_id,
                name=deactivated.name,
                kind=deactivated.kind,
                include_in_summaries=deactivated.include_in_summaries,
                is_fixed=deactivated.is_fixed,
                is_active=deactivated.is_active,
            )
        )