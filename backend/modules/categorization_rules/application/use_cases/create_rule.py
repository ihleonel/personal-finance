from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from modules.categorization_rules.application.dtos import (
    CategorizationRuleOutput,
    CreateCategorizationRuleInput,
)
from modules.categorization_rules.domain.repositories import (
    CategorizationRuleRepository,
)
from modules.categorization_rules.domain.value_objects import (
    RuleKind,
    RuleMatchType,
    RulePattern,
    max_pattern_length,
)
from modules.shared.application.result import Result


@dataclass
class CreateCategorizationRuleUseCase:
    repository: CategorizationRuleRepository

    def execute(
        self, data: CreateCategorizationRuleInput
    ) -> Result[CategorizationRuleOutput]:
        result = Result[CategorizationRuleOutput]()

        if not data.pattern or not data.pattern.strip():
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

        match_type_vo = RuleMatchType.try_parse(data.match_type)
        if match_type_vo is None:
            result.add_error(
                "match_type",
                "categorization_rules.match_type.invalid",
                str(_("El tipo de coincidencia no es válido. Valores admitidos: contains, equals.")),
            )

        kind_vo = RuleKind.try_parse(data.kind)
        if kind_vo is None:
            result.add_error(
                "kind",
                "categorization_rules.kind.invalid",
                str(_("El tipo de categoría no es válido. Valores admitidos: income, expense.")),
            )

        if data.category_id is None or data.category_id <= 0:
            result.add_error(
                "category_id",
                "categorization_rules.category_id.invalid",
                str(_("La categoría es obligatoria.")),
            )

        if data.priority is None or data.priority < 0:
            result.add_error(
                "priority",
                "categorization_rules.priority.invalid",
                str(_("La prioridad debe ser un número entero no negativo.")),
            )

        if (
            data.pattern
            and data.pattern.strip()
            and match_type_vo is not None
            and self.repository.exists_active_duplicate_for_owner(
                owner_id=data.owner_id,
                pattern=data.pattern,
                match_type=match_type_vo.value,
            )
        ):
            result.add_error(
                "pattern",
                "categorization_rules.pattern.already_exists",
                str(_("Ya tenés una regla activa con ese patrón y tipo de coincidencia.")),
            )

        if result.has_errors:
            return result

        try:
            saved = self.repository.save(
                owner_id=data.owner_id,
                pattern=data.pattern,
                match_type=match_type_vo.value,  # type: ignore[union-attr]
                category_id=data.category_id,
                kind=kind_vo.value,  # type: ignore[union-attr]
                priority=data.priority,
            )
        except ValueError as exc:
            result.add_error(
                "non_field_errors",
                "categorization_rules.rule.invalid",
                str(_("No se pudo crear la regla.")),
            )
            return result

        return Result.ok(self._to_output(saved))

    @staticmethod
    def _to_output(rule) -> CategorizationRuleOutput:
        return CategorizationRuleOutput(
            id=rule.id or 0,
            owner_id=rule.owner_id,
            pattern=rule.pattern,
            match_type=rule.match_type,
            category_id=rule.category_id,
            kind=rule.kind,
            priority=rule.priority,
            is_active=rule.is_active,
        )