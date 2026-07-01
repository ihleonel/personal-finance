from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.utils.translation import gettext_lazy as _

from modules.categorization_rules.application.dtos import (
    CategorizationRuleOutput,
    UpdateCategorizationRuleInput,
)
from modules.categorization_rules.domain.repositories import (
    CategorizationRuleRepository,
)
from modules.categorization_rules.domain.value_objects import (
    RuleKind,
    RuleMatchType,
    max_pattern_length,
)
from modules.shared.application.result import Result


@dataclass
class UpdateCategorizationRuleUseCase:
    repository: CategorizationRuleRepository

    def execute(
        self,
        owner_id: int,
        rule_id: int,
        data: UpdateCategorizationRuleInput,
    ) -> Result[CategorizationRuleOutput]:
        result = Result[CategorizationRuleOutput]()

        rule = self.repository.find_by_id(rule_id)
        if rule is None or rule.owner_id != owner_id:
            result.add_error(
                "non_field_errors",
                "categorization_rules.rule.not_found",
                str(_("Regla no encontrada.")),
            )
            return result

        if not rule.is_active:
            result.add_error(
                "non_field_errors",
                "categorization_rules.rule.inactive",
                str(_("La regla está inactiva y no se puede editar.")),
            )
            return result

        has_any_field = any(
            getattr(data, f) is not None
            for f in ("pattern", "match_type", "category_id", "kind", "priority")
        )
        if not has_any_field:
            result.add_error(
                "non_field_errors",
                "categorization_rules.rule.empty_payload",
                str(_("Proporciona al menos un campo para actualizar.")),
            )
            return result

        new_pattern: Optional[str] = None
        new_match_type: Optional[str] = None
        new_category_id: Optional[int] = None
        new_kind: Optional[str] = None
        new_priority: Optional[int] = None

        if data.pattern is not None:
            if not data.pattern.strip():
                result.add_error(
                    "pattern",
                    "categorization_rules.pattern.required",
                    str(_("El patrón es obligatorio.")),
                )
            elif len(data.pattern) > max_pattern_length:
                result.add_error(
                    "pattern",
                    "categorization_rules.pattern.max_length",
                    str(_(f"El patrón no puede tener más de {max_pattern_length} caracteres.")),
                )
            new_pattern = data.pattern

        if data.match_type is not None:
            parsed_match = RuleMatchType.try_parse(data.match_type)
            if parsed_match is None:
                result.add_error(
                    "match_type",
                    "categorization_rules.match_type.invalid",
                    str(_("El tipo de coincidencia no es válido. Valores admitidos: contains, equals.")),
                )
            new_match_type = parsed_match.value if parsed_match is not None else None

        if data.kind is not None:
            parsed_kind = RuleKind.try_parse(data.kind)
            if parsed_kind is None:
                result.add_error(
                    "kind",
                    "categorization_rules.kind.invalid",
                    str(_("El tipo de categoría no es válido. Valores admitidos: income, expense.")),
                )
            new_kind = parsed_kind.value if parsed_kind is not None else None

        if data.category_id is not None and data.category_id <= 0:
            result.add_error(
                "category_id",
                "categorization_rules.category_id.invalid",
                str(_("La categoría es obligatoria.")),
            )
        new_category_id = data.category_id

        if data.priority is not None and data.priority < 0:
            result.add_error(
                "priority",
                "categorization_rules.priority.invalid",
                str(_("La prioridad debe ser un número entero no negativo.")),
            )
        new_priority = data.priority

        candidate_pattern = new_pattern if new_pattern is not None else rule.pattern
        candidate_match = new_match_type if new_match_type is not None else rule.match_type
        if (
            (new_pattern is not None or new_match_type is not None)
            and candidate_pattern != rule.pattern
            or (new_match_type is not None and candidate_match != rule.match_type)
        ):
            if self.repository.exists_active_duplicate_for_owner(
                owner_id=owner_id,
                pattern=candidate_pattern,
                match_type=candidate_match,
                exclude_id=rule_id,
            ):
                result.add_error(
                    "pattern",
                    "categorization_rules.pattern.already_exists",
                    str(_("Ya tenés una regla activa con ese patrón y tipo de coincidencia.")),
                )

        if result.has_errors:
            return result

        updated = self.repository.update(
            rule_id=rule_id,
            pattern=new_pattern,
            match_type=new_match_type,
            category_id=new_category_id,
            kind=new_kind,
            priority=new_priority,
        )

        return Result.ok(
            CategorizationRuleOutput(
                id=updated.id or 0,
                owner_id=updated.owner_id,
                pattern=updated.pattern,
                match_type=updated.match_type,
                category_id=updated.category_id,
                kind=updated.kind,
                priority=updated.priority,
                is_active=updated.is_active,
            )
        )