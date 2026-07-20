"""Unit tests for DeleteTransactionUseCase."""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from django.utils import translation

from modules.transactions.application.use_cases.delete_transaction import (
    DeleteTransactionUseCase,
)

from tests.fakes import InMemoryTransactionRepository


class TestDeleteTransactionUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryTransactionRepository()
        self.use_case = DeleteTransactionUseCase(repository=self.repo)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_deletes_transaction(self) -> None:
        tx = self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        result = self.use_case.execute(owner_id=1, transaction_id=tx.id)
        self.assertTrue(result.is_success)
        self.assertIsNone(self.repo.find_by_id(tx.id))

    def test_fails_when_transaction_not_found(self) -> None:
        result = self.use_case.execute(owner_id=1, transaction_id=9999)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transaction.not_found")

    def test_fails_when_transaction_belongs_to_other_user(self) -> None:
        tx = self.repo.seed(
            owner_id=2, account_id=20, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        result = self.use_case.execute(owner_id=1, transaction_id=tx.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transaction.not_found")

    def test_deletes_both_transfer_transactions(self) -> None:
        tx1 = self.repo.seed(
            owner_id=1, account_id=10, kind="expense",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        tx2 = self.repo.seed(
            owner_id=1, account_id=20, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        result = self.use_case.execute(owner_id=1, transaction_id=tx1.id)
        self.assertTrue(result.is_success)
        self.assertIsNone(self.repo.find_by_id(tx1.id))
        self.assertIsNotNone(self.repo.find_by_id(tx2.id))

    def test_deleting_one_side_removes_entire_group(self) -> None:
        tx1 = self.repo.seed(
            owner_id=1, account_id=10, kind="expense",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        tx2 = self.repo.seed(
            owner_id=1, account_id=20, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        self.use_case.execute(owner_id=1, transaction_id=tx2.id)
        self.assertIsNotNone(self.repo.find_by_id(tx1.id))
        self.assertIsNone(self.repo.find_by_id(tx2.id))