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
from modules.shared.application.result import Result


@dataclass
class ListCategorizationRulesUseCase:
    repository: CategorizationRuleRepository

    def execute(self, owner_id: int) -> Result[list[CategorizationRuleOutput]]:
        rules = self.repository.list_by_owner(owner_id)
        outputs = [self._to_output(r) for r in rules]
        return Result.ok(outputs)

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