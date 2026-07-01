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
class GetCategorizationRuleUseCase:
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

        return Result.ok(
            CategorizationRuleOutput(
                id=rule.id or 0,
                owner_id=rule.owner_id,
                pattern=rule.pattern,
                match_type=rule.match_type,
                category_id=rule.category_id,
                kind=rule.kind,
                priority=rule.priority,
                is_active=rule.is_active,
            )
        )