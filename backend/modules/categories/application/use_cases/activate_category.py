from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from modules.categories.application.dtos import CategoryOutput
from modules.categories.domain.repositories import CategoryRepository
from modules.shared.application.result import Result


@dataclass
class ActivateCategoryUseCase:
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

        if category.is_active:
            result.add_error(
                "non_field_errors",
                "categories.category.already_active",
                str(_("La categoría ya está activa.")),
            )
            return result

        activated = self.repository.activate(category_id)
        return Result.ok(
            CategoryOutput(
                id=activated.id or 0,
                owner_id=activated.owner_id,
                name=activated.name,
                kind=activated.kind,
                is_active=activated.is_active,
            )
        )