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
class DeleteCategorizationRuleUseCase:
    repository: CategorizationRuleRepository

    def execute(self, owner_id: int, rule_id: int) -> Result[bool]:
        result = Result[bool]()

        rule = self.repository.find_by_id(rule_id)
        if rule is None or rule.owner_id != owner_id:
            result.add_error(
                "non_field_errors",
                "categorization_rules.rule.not_found",
                str(_("Regla no encontrada.")),
            )
            return result

        self.repository.delete(rule_id)
        return Result.ok(True)