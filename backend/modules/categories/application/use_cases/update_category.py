from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.utils.translation import gettext_lazy as _

from modules.categories.application.dtos import CategoryOutput, UpdateCategoryInput
from modules.categories.domain.repositories import CategoryRepository
from modules.categories.domain.value_objects import CategoryKind
from modules.shared.application.result import Result


_MAX_NAME_LENGTH = 100


@dataclass
class UpdateCategoryUseCase:
    repository: CategoryRepository

    def execute(
        self, owner_id: int, category_id: int, data: UpdateCategoryInput
    ) -> Result[CategoryOutput]:
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
                "categories.category.inactive",
                str(_("La categoría está inactiva y no se puede editar.")),
            )
            return result

        has_any_field = any(
            getattr(data, f) is not None
            for f in ("name", "kind", "include_in_summaries", "is_fixed")
        )
        if not has_any_field:
            result.add_error(
                "non_field_errors",
                "categories.category.empty_payload",
                str(_("Proporciona al menos un campo para actualizar.")),
            )
            return result

        new_name: Optional[str] = None
        new_kind: Optional[str] = None
        new_include_in_summaries: Optional[bool] = None
        new_is_fixed: Optional[bool] = None

        if data.name is not None:
            if not data.name.strip():
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
            new_name = data.name

        if data.kind is not None:
            parsed_kind = CategoryKind.try_parse(data.kind)
            if parsed_kind is None:
                result.add_error(
                    "kind",
                    "categories.kind.invalid",
                    str(_("El tipo de categoría no es válido. Valores admitidos: income, expense.")),
                )
            new_kind = parsed_kind.value if parsed_kind is not None else None

        if data.include_in_summaries is not None:
            new_include_in_summaries = data.include_in_summaries

        if data.is_fixed is not None:
            new_is_fixed = data.is_fixed

        if (
            new_name is not None
            and new_name != category.name
            and self.repository.exists_active_name_for_owner(owner_id, new_name)
        ):
            result.add_error(
                "name",
                "categories.name.already_exists",
                str(_("Ya tenés una categoría activa con ese nombre.")),
            )

        if result.has_errors:
            return result

        updated = self.repository.update(
            category_id=category_id,
            name=new_name,
            kind=new_kind,
            include_in_summaries=new_include_in_summaries,
            is_fixed=new_is_fixed,
        )

        return Result.ok(
            CategoryOutput(
                id=updated.id or 0,
                owner_id=updated.owner_id,
                name=updated.name,
                kind=updated.kind,
                include_in_summaries=updated.include_in_summaries,
                is_fixed=updated.is_fixed,
                is_active=updated.is_active,
            )
        )