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
class DeactivateCategorizationRuleUseCase:
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

        if not rule.is_active:
            result.add_error(
                "non_field_errors",
                "categorization_rules.rule.already_inactive",
                str(_("La regla ya está inactiva.")),
            )
            return result

        deactivated = self.repository.deactivate(rule_id)
        return Result.ok(
            CategorizationRuleOutput(
                id=deactivated.id or 0,
                owner_id=deactivated.owner_id,
                pattern=deactivated.pattern,
                match_type=deactivated.match_type,
                category_id=deactivated.category_id,
                kind=deactivated.kind,
                priority=deactivated.priority,
                is_active=deactivated.is_active,
            )
        )