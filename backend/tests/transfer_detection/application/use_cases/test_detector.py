"""Unit tests for TransferCandidateDetector and TransferPairMatcher."""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from modules.transfer_detection.application.detector import (
    TransferCandidateDetector,
    TransferPairMatcher,
)

from tests.fakes import (
    InMemoryTransactionRepository,
)


class TestTransferCandidateDetector(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = TransferCandidateDetector()
        self.rules = [
            type("R", (), {
                "pattern": "transferencia",
                "match_type": "contains",
                "is_active": True,
            })(),
            type("R", (), {
                "pattern": "movimiento interno",
                "match_type": "equals",
                "is_active": True,
            })(),
        ]

    def test_contains_match_returns_true(self) -> None:
        self.assertTrue(
            self.detector.is_transfer_candidate(
                "Transferencia entre cuentas", self.rules
            )
        )

    def test_equals_match_returns_true(self) -> None:
        self.assertTrue(
            self.detector.is_transfer_candidate(
                "Movimiento interno", self.rules
            )
        )

    def test_no_match_returns_false(self) -> None:
        self.assertFalse(
            self.detector.is_transfer_candidate("Compra en tienda", self.rules)
        )

    def test_normalization_ignores_diacritics_and_digits(self) -> None:
        self.assertTrue(
            self.detector.is_transfer_candidate(
                "Transferencia 12345 CTA", self.rules
            )
        )

    def test_empty_description_returns_false(self) -> None:
        self.assertFalse(self.detector.is_transfer_candidate("", self.rules))

    def test_empty_rules_returns_false(self) -> None:
        self.assertFalse(
            self.detector.is_transfer_candidate("Transferencia", [])
        )

    def test_inactive_rule_is_ignored(self) -> None:
        rules = [
            type("R", (), {
                "pattern": "transferencia",
                "match_type": "contains",
                "is_active": False,
            })(),
        ]
        self.assertFalse(
            self.detector.is_transfer_candidate("Transferencia", rules)
        )


class TestTransferPairMatcher(unittest.TestCase):
    def setUp(self) -> None:
        self.matcher = TransferPairMatcher()
        self.repo = InMemoryTransactionRepository()
        self.account_a = 1
        self.account_b = 2

    def _seed(self, kind: str, amount: str, d: date, account_id: int, desc: str = ""):
        return self.repo.seed(
            owner_id=1,
            account_id=account_id,
            kind=kind,
            amount=Decimal(amount),
            date=d,
            description=desc,
        )

    def test_valid_pair_yields_suggestion(self) -> None:
        d = date(2026, 6, 1)
        exp = self._seed("expense", "100.00", d, self.account_a)
        inc = self._seed("income", "100.00", d, self.account_b)
        suggestions = self.matcher.match(self.repo._by_id.values())
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].source_id, exp.id)
        self.assertEqual(suggestions[0].destination_id, inc.id)

    def test_same_account_does_not_match(self) -> None:
        d = date(2026, 6, 1)
        self._seed("expense", "100.00", d, self.account_a)
        self._seed("income", "100.00", d, self.account_a)
        suggestions = self.matcher.match(self.repo._by_id.values())
        self.assertEqual(suggestions, [])

    def test_amount_outside_tolerance_does_not_match(self) -> None:
        d = date(2026, 6, 1)
        self._seed("expense", "100.00", d, self.account_a)
        self._seed("income", "100.50", d, self.account_b)
        suggestions = self.matcher.match(
            self.repo._by_id.values(), amount_tolerance="0.00"
        )
        self.assertEqual(suggestions, [])

    def test_amount_within_tolerance_matches(self) -> None:
        d = date(2026, 6, 1)
        self._seed("expense", "100.00", d, self.account_a)
        self._seed("income", "100.50", d, self.account_b)
        suggestions = self.matcher.match(
            self.repo._by_id.values(), amount_tolerance="0.50"
        )
        self.assertEqual(len(suggestions), 1)

    def test_date_outside_window_does_not_match(self) -> None:
        self._seed("expense", "100.00", date(2026, 6, 1), self.account_a)
        self._seed("income", "100.00", date(2026, 6, 10), self.account_b)
        suggestions = self.matcher.match(
            self.repo._by_id.values(), window_days=3
        )
        self.assertEqual(suggestions, [])

    def test_linked_transaction_is_excluded(self) -> None:
        group = uuid4()
        self._seed("expense", "100.00", date(2026, 6, 1), self.account_a)
        self.repo.seed(
            owner_id=1,
            account_id=self.account_b,
            kind="income",
            amount=Decimal("100.00"),
            date=date(2026, 6, 1),
            transfer_group_id=group,
        )
        suggestions = self.matcher.match(self.repo._by_id.values())
        self.assertEqual(suggestions, [])

    def test_each_transaction_appears_at_most_once(self) -> None:
        d = date(2026, 6, 1)
        self._seed("expense", "100.00", d, self.account_a)
        self._seed("income", "100.00", d, self.account_b)
        self._seed("income", "100.00", d, account_id=3)
        suggestions = self.matcher.match(self.repo._by_id.values())
        self.assertEqual(len(suggestions), 1)

    def test_require_both_candidates_filters(self) -> None:
        d = date(2026, 6, 1)
        exp = self._seed("expense", "100.00", d, self.account_a, desc="transferencia")
        inc = self._seed("income", "100.00", d, self.account_b, desc="compra")
        candidate_ids = {exp.id}
        suggestions = self.matcher.match(
            self.repo._by_id.values(),
            require_both_candidates=True,
            candidate_ids=candidate_ids,
        )
        self.assertEqual(suggestions, [])


if __name__ == "__main__":
    unittest.main()