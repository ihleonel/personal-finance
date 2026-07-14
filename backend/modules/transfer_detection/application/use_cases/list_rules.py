from __future__ import annotations

from dataclasses import dataclass

from modules.shared.application.result import Result
from modules.transfer_detection.application.dtos import (
    TransferDetectionRuleOutput,
)
from modules.transfer_detection.domain.repositories import (
    TransferDetectionRuleRepository,
)


@dataclass
class ListTransferDetectionRulesUseCase:
    repository: TransferDetectionRuleRepository

    def execute(self, owner_id: int) -> Result[list[TransferDetectionRuleOutput]]:
        rules = self.repository.list_by_owner(owner_id)
        outputs = [self._to_output(r) for r in rules]
        return Result.ok(outputs)

    @staticmethod
    def _to_output(rule) -> TransferDetectionRuleOutput:
        return TransferDetectionRuleOutput(
            id=rule.id or 0,
            owner_id=rule.owner_id,
            pattern=rule.pattern,
            match_type=rule.match_type,
            priority=rule.priority,
            is_active=rule.is_active,
        )