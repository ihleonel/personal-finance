from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_type
from typing import Optional

from django.utils.translation import gettext_lazy as _

from modules.shared.application.result import Result
from modules.transfer_detection.application.detector import (
    TransferCandidateDetector,
    TransferPairMatcher,
)
from modules.transfer_detection.application.dtos import (
    DetectTransfersInput,
    DetectTransfersOutput,
    TransferPairSuggestionOutput,
)
from modules.transfer_detection.application.ports import TransactionQueryPort
from modules.transfer_detection.domain.repositories import (
    TransferDetectionRuleRepository,
)
from modules.transfer_detection.domain.value_objects import (
    AmountTolerance,
    DateWindowDays,
)


@dataclass
class DetectTransfersUseCase:
    transaction_query: TransactionQueryPort
    rule_repository: TransferDetectionRuleRepository
    candidate_detector: TransferCandidateDetector
    pair_matcher: TransferPairMatcher

    def execute(self, data: DetectTransfersInput) -> Result[DetectTransfersOutput]:
        result = Result[DetectTransfersOutput]()

        date_from = self._parse_date(data.date_from)
        date_to = self._parse_date(data.date_to)

        if data.date_from is not None and date_from is None:
            result.add_error(
                "date_from",
                "transfer_detection.date_from.invalid",
                str(_("La fecha desde no es válida.")),
            )
        if data.date_to is not None and date_to is None:
            result.add_error(
                "date_to",
                "transfer_detection.date_to.invalid",
                str(_("La fecha hasta no es válida.")),
            )

        window_vo = DateWindowDays.try_parse(data.window_days)
        if window_vo is None:
            result.add_error(
                "window_days",
                "transfer_detection.window_days.invalid",
                str(_("La ventana de días debe ser un entero entre 0 y 30.")),
            )

        try:
            AmountTolerance(data.amount_tolerance)
        except ValueError:
            result.add_error(
                "amount_tolerance",
                "transfer_detection.amount_tolerance.invalid",
                str(_("La tolerancia de monto no es válida.")),
            )

        if result.has_errors:
            return result

        transactions = self.transaction_query.list_unlinked_by_owner(
            owner_id=data.owner_id,
            account_id=data.account_id,
            date_from=date_from,
            date_to=date_to,
        )

        rules = self.rule_repository.list_active_by_owner(data.owner_id)
        candidate_ids = {
            t.id
            for t in transactions
            if self.candidate_detector.is_transfer_candidate(t.description, rules)
        }

        suggestions = self.pair_matcher.match(
            transactions,
            window_days=window_vo.value if window_vo is not None else 3,  # type: ignore[union-attr]
            amount_tolerance=data.amount_tolerance,
            require_both_candidates=False,
            candidate_ids=candidate_ids,
        )

        outputs = [
            TransferPairSuggestionOutput(
                source_id=s.source_id,
                destination_id=s.destination_id,
                amount=s.amount,
                source_account_id=s.source_account_id,
                destination_account_id=s.destination_account_id,
                source_date=s.source_date.isoformat() if hasattr(s.source_date, "isoformat") else str(s.source_date),
                destination_date=s.destination_date.isoformat() if hasattr(s.destination_date, "isoformat") else str(s.destination_date),
                score=s.score,
                matched_by=s.matched_by,
            )
            for s in suggestions
        ]
        return Result.ok(DetectTransfersOutput(suggestions=outputs))

    @staticmethod
    def _parse_date(raw: Optional[str]) -> Optional[date_type]:
        if raw is None or raw == "":
            return None
        try:
            return date_type.fromisoformat(raw)
        except ValueError:
            return None