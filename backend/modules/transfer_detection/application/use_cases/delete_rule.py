from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from modules.shared.application.result import Result
from modules.transfer_detection.application.dtos import (
    TransferDetectionRuleOutput,
)
from modules.transfer_detection.domain.repositories import (
    TransferDetectionRuleRepository,
)


@dataclass
class DeleteTransferDetectionRuleUseCase:
    repository: TransferDetectionRuleRepository

    def execute(self, owner_id: int, rule_id: int) -> Result[bool]:
        result = Result[bool]()

        rule = self.repository.find_by_id(rule_id)
        if rule is None or rule.owner_id != owner_id:
            result.add_error(
                "non_field_errors",
                "transfer_detection.rule.not_found",
                str(_("Regla no encontrada.")),
            )
            return result

        self.repository.delete(rule_id)
        return Result.ok(True)