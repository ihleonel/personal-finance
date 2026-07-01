from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from modules.categorization_rules.application.dtos import (
    CategorizationRuleOutput,
)
from modules.categorization_rules.domain.repositories import (
    CategorizationRuleRepository,
)
from modules.shared.application.result import Result


@dataclass
class ActivateCategorizationRuleUseCase:
    repository: CategorizationRuleRepository

    def execute(self, owner_id: int, rule_id: int) -> Result[CategorizationRuleOutput]:
        result = Result[CategorizationRuleOutput]()

        rule = self.repository.find_by_id(rule_id)
        if rule is None or rule.owner_id != owner_id:
            result.add_error(
                "non_field_errors",
                "categorization_rules.rule.not_found",
                str(_("Regla no encontrada.")),
            )
            return result

        if rule.is_active:
            result.add_error(
                "non_field_errors",
                "categorization_rules.rule.already_active",
                str(_("La regla ya está activa.")),
            )
            return result

        if self.repository.exists_active_duplicate_for_owner(
            owner_id=owner_id,
            pattern=rule.pattern,
            match_type=rule.match_type,
            exclude_id=rule_id,
        ):
            result.add_error(
                "non_field_errors",
                "categorization_rules.pattern.already_exists",
                str(_("Ya tenés una regla activa con ese patrón y tipo de coincidencia.")),
            )
            return result

        activated = self.repository.activate(rule_id)
        return Result.ok(
            CategorizationRuleOutput(
                id=activated.id or 0,
                owner_id=activated.owner_id,
                pattern=activated.pattern,
                match_type=activated.match_type,
                category_id=activated.category_id,
                kind=activated.kind,
                priority=activated.priority,
                is_active=activated.is_active,
            )
        )