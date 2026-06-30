from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from modules.categories.application.dtos import CategoryOutput, CreateCategoryInput
from modules.categories.domain.repositories import CategoryRepository
from modules.categories.domain.value_objects import CategoryKind
from modules.shared.application.result import Result


_MAX_NAME_LENGTH = 100


@dataclass
class CreateCategoryUseCase:
    repository: CategoryRepository

    def execute(self, data: CreateCategoryInput) -> Result[CategoryOutput]:
        result = Result[CategoryOutput]()

        if not data.name or not data.name.strip():
            result.add_error(
                "name",
                "categories.name.required",
                str(_("El nombre de la categoría es obligatorio.")),
            )
        elif len(data.name) > _MAX_NAME_LENGTH:
            result.add_error(
                "name",
                "categories.name.max_length",
                str(_("Asegúrate de que el nombre no tenga más de 100 caracteres.")),
            )

        kind = CategoryKind.try_parse(data.kind)
        if kind is None:
            result.add_error(
                "kind",
                "categories.kind.invalid",
                str(_("El tipo de categoría no es válido. Valores admitidos: income, expense.")),
            )

        if (
            data.name
            and data.name.strip()
            and self.repository.exists_active_name_for_owner(data.owner_id, data.name)
        ):
            result.add_error(
                "name",
                "categories.name.already_exists",
                str(_("Ya tenés una categoría activa con ese nombre.")),
            )

        if result.has_errors:
            return result

        saved = self.repository.save(
            owner_id=data.owner_id,
            name=data.name,
            kind=kind.value,  # type: ignore[union-attr]
        )

        return Result.ok(self._to_output(saved))

    @staticmethod
    def _to_output(category) -> CategoryOutput:
        return CategoryOutput(
            id=category.id or 0,
            owner_id=category.owner_id,
            name=category.name,
            kind=category.kind,
            is_active=category.is_active,
        )