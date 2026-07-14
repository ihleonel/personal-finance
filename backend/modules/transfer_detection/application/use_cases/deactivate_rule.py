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
class DeactivateTransferDetectionRuleUseCase:
    repository: TransferDetectionRuleRepository

    def execute(self, owner_id: int, rule_id: int) -> Result[TransferDetectionRuleOutput]:
        result = Result[TransferDetectionRuleOutput]()

        rule = self.repository.find_by_id(rule_id)
        if rule is None or rule.owner_id != owner_id:
            result.add_error(
                "non_field_errors",
                "transfer_detection.rule.not_found",
                str(_("Regla no encontrada.")),
            )
            return result

        if not rule.is_active:
            result.add_error(
                "non_field_errors",
                "transfer_detection.rule.already_inactive",
                str(_("La regla ya está inactiva.")),
            )
            return result

        deactivated = self.repository.deactivate(rule_id)
        return Result.ok(
            TransferDetectionRuleOutput(
                id=deactivated.id or 0,
                owner_id=deactivated.owner_id,
                pattern=deactivated.pattern,
                match_type=deactivated.match_type,
                priority=deactivated.priority,
                is_active=deactivated.is_active,
            )
        )