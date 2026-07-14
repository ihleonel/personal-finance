"""Unit tests for SuggestTransferUseCase and DetectTransfersUseCase."""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from django.utils import translation

from modules.transfer_detection.application.detector import (
    TransferCandidateDetector,
    TransferPairMatcher,
)
from modules.transfer_detection.application.dtos import (
    DetectTransfersInput,
    SuggestTransferInput,
)
from modules.transfer_detection.application.use_cases.detect_transfers import (
    DetectTransfersUseCase,
)
from modules.transfer_detection.application.use_cases.suggest_transfer import (
    SuggestTransferUseCase,
)

from tests.fakes import (
    FakeTransactionQueryPort,
    InMemoryTransactionRepository,
    InMemoryTransferDetectionRuleRepository,
)


class TestSuggestTransferUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.rule_repo = InMemoryTransferDetectionRuleRepository()
        self.rule_repo.seed(
            owner_id=1, pattern="transferencia", match_type="contains", priority=5
        )
        self.use_case = SuggestTransferUseCase(
            rule_repository=self.rule_repo,
            candidate_detector=TransferCandidateDetector(),
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_returns_true_for_matching_description(self) -> None:
        result = self.use_case.execute(
            SuggestTransferInput(owner_id=1, description="Transferencia entre cuentas")
        )
        self.assertTrue(result.is_success)
        self.assertTrue(result.value.is_transfer)

    def test_returns_false_for_non_matching_description(self) -> None:
        result = self.use_case.execute(
            SuggestTransferInput(owner_id=1, description="Compra en super")
        )
        self.assertTrue(result.is_success)
        self.assertFalse(result.value.is_transfer)

    def test_no_rules_returns_false(self) -> None:
        rule_repo = InMemoryTransferDetectionRuleRepository()
        use_case = SuggestTransferUseCase(
            rule_repository=rule_repo,
            candidate_detector=TransferCandidateDetector(),
        )
        result = use_case.execute(
            SuggestTransferInput(owner_id=1, description="Transferencia")
        )
        self.assertTrue(result.is_success)
        self.assertFalse(result.value.is_transfer)


class TestDetectTransfersUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.tx_repo = InMemoryTransactionRepository()
        self.rule_repo = InMemoryTransferDetectionRuleRepository()
        self.use_case = DetectTransfersUseCase(
            transaction_query=FakeTransactionQueryPort(self.tx_repo),
            rule_repository=self.rule_repo,
            candidate_detector=TransferCandidateDetector(),
            pair_matcher=TransferPairMatcher(),
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def _seed(self, kind: str, amount: str, d: date, account_id: int, desc: str = ""):
        return self.tx_repo.seed(
            owner_id=1,
            account_id=account_id,
            kind=kind,
            amount=Decimal(amount),
            date=d,
            description=desc,
        )

    def test_valid_pair_detected(self) -> None:
        d = date(2026, 6, 1)
        exp = self._seed("expense", "100.00", d, 1, desc="transferencia")
        inc = self._seed("income", "100.00", d, 2, desc="transferencia")
        result = self.use_case.execute(DetectTransfersInput(owner_id=1))
        self.assertTrue(result.is_success)
        self.assertEqual(len(result.value.suggestions), 1)
        self.assertEqual(result.value.suggestions[0].source_id, exp.id)
        self.assertEqual(result.value.suggestions[0].destination_id, inc.id)

    def test_same_account_not_detected(self) -> None:
        d = date(2026, 6, 1)
        self._seed("expense", "100.00", d, 1, desc="transferencia")
        self._seed("income", "100.00", d, 1, desc="transferencia")
        result = self.use_case.execute(DetectTransfersInput(owner_id=1))
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.suggestions, [])

    def test_amount_outside_tolerance_not_detected(self) -> None:
        d = date(2026, 6, 1)
        self._seed("expense", "100.00", d, 1, desc="transferencia")
        self._seed("income", "100.50", d, 2, desc="transferencia")
        result = self.use_case.execute(
            DetectTransfersInput(owner_id=1, amount_tolerance="0.00")
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.suggestions, [])

    def test_date_outside_window_not_detected(self) -> None:
        self._seed("expense", "100.00", date(2026, 6, 1), 1, desc="transferencia")
        self._seed("income", "100.00", date(2026, 6, 10), 2, desc="transferencia")
        result = self.use_case.execute(
            DetectTransfersInput(owner_id=1, window_days=3)
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.suggestions, [])

    def test_linked_transaction_excluded(self) -> None:
        from uuid import uuid4

        group = uuid4()
        self.tx_repo.seed(
            owner_id=1, account_id=1, kind="expense",
            amount=Decimal("100.00"), date=date(2026, 6, 1),
            transfer_group_id=group, description="transferencia",
        )
        self._seed("income", "100.00", date(2026, 6, 1), 2, desc="transferencia")
        result = self.use_case.execute(DetectTransfersInput(owner_id=1))
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.suggestions, [])

    def test_invalid_window_days_returns_error(self) -> None:
        result = self.use_case.execute(
            DetectTransfersInput(owner_id=1, window_days=99)
        )
        self.assertFalse(result.is_success)
        codes = [e.code for e in result.errors]
        self.assertIn("transfer_detection.window_days.invalid", codes)

    def test_invalid_amount_tolerance_returns_error(self) -> None:
        result = self.use_case.execute(
            DetectTransfersInput(owner_id=1, amount_tolerance="abc")
        )
        self.assertFalse(result.is_success)
        codes = [e.code for e in result.errors]
        self.assertIn("transfer_detection.amount_tolerance.invalid", codes)

    def test_account_filter_applied(self) -> None:
        d = date(2026, 6, 1)
        self._seed("expense", "100.00", d, 1, desc="transferencia")
        self._seed("income", "100.00", d, 2, desc="transferencia")
        self._seed("expense", "200.00", d, 3, desc="transferencia")
        self._seed("income", "200.00", d, 4, desc="transferencia")
        result = self.use_case.execute(
            DetectTransfersInput(owner_id=1, account_id=1)
        )
        self.assertTrue(result.is_success)
        self.assertEqual(len(result.value.suggestions), 0)


if __name__ == "__main__":
    unittest.main()