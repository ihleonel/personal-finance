"""Unit tests for GetTransactionUseCase."""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from django.utils import translation

from modules.transactions.application.use_cases.get_transaction import (
    GetTransactionUseCase,
)

from tests.fakes import InMemoryTransactionRepository


class TestGetTransactionUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryTransactionRepository()
        self.use_case = GetTransactionUseCase(repository=self.repo)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_returns_transaction_when_owned(self) -> None:
        tx = self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
            description="Salario",
        )
        result = self.use_case.execute(owner_id=1, transaction_id=tx.id)
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.id, tx.id)
        self.assertEqual(result.value.amount, "100.00")
        self.assertEqual(result.value.description, "Salario")

    def test_fails_when_transaction_does_not_exist(self) -> None:
        result = self.use_case.execute(owner_id=1, transaction_id=9999)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transaction.not_found")
        self.assertEqual(result.errors[0].message, "Transacción no encontrada.")

    def test_fails_when_transaction_belongs_to_other_user(self) -> None:
        tx = self.repo.seed(
            owner_id=2, account_id=20, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        result = self.use_case.execute(owner_id=1, transaction_id=tx.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transaction.not_found")