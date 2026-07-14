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
class ActivateTransferDetectionRuleUseCase:
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

        if rule.is_active:
            result.add_error(
                "non_field_errors",
                "transfer_detection.rule.already_active",
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
                "transfer_detection.pattern.already_exists",
                str(_("Ya tenés una regla activa con ese patrón y tipo de coincidencia.")),
            )
            return result

        activated = self.repository.activate(rule_id)
        return Result.ok(
            TransferDetectionRuleOutput(
                id=activated.id or 0,
                owner_id=activated.owner_id,
                pattern=activated.pattern,
                match_type=activated.match_type,
                priority=activated.priority,
                is_active=activated.is_active,
            )
        )