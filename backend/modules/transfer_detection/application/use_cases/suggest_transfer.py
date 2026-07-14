from __future__ import annotations

from dataclasses import dataclass

from modules.shared.application.result import Result
from modules.transfer_detection.application.detector import (
    TransferCandidateDetector,
)
from modules.transfer_detection.application.dtos import (
    SuggestTransferInput,
    SuggestTransferOutput,
)
from modules.transfer_detection.domain.repositories import (
    TransferDetectionRuleRepository,
)


@dataclass
class SuggestTransferUseCase:
    rule_repository: TransferDetectionRuleRepository
    candidate_detector: TransferCandidateDetector

    def execute(self, data: SuggestTransferInput) -> Result[SuggestTransferOutput]:
        rules = self.rule_repository.list_active_by_owner(data.owner_id)
        is_transfer = self.candidate_detector.is_transfer_candidate(
            data.description, rules
        )
        return Result.ok(SuggestTransferOutput(is_transfer=is_transfer))