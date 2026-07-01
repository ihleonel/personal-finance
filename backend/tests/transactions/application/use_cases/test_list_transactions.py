"""Unit tests for ListTransactionsUseCase."""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from django.utils import translation

from modules.transactions.application.dtos import ListTransactionsFilters
from modules.transactions.application.use_cases.list_transactions import (
    ListTransactionsUseCase,
)

from tests.fakes import InMemoryTransactionRepository


class TestListTransactionsUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryTransactionRepository()
        self.use_case = ListTransactionsUseCase(repository=self.repo)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_returns_empty_when_no_transactions(self) -> None:
        result = self.use_case.execute(owner_id=1)
        self.assertTrue(result.is_success)
        self.assertEqual(result.value, [])

    def test_returns_only_owned_transactions(self) -> None:
        self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        self.repo.seed(
            owner_id=2, account_id=20, kind="expense",
            amount=Decimal("50"), date=date(2026, 1, 1),
        )
        result = self.use_case.execute(owner_id=1)
        self.assertTrue(result.is_success)
        self.assertEqual(len(result.value), 1)
        self.assertEqual(result.value[0].owner_id, 1)

    def test_filters_by_account(self) -> None:
        self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        self.repo.seed(
            owner_id=1, account_id=20, kind="income",
            amount=Decimal("200"), date=date(2026, 1, 2),
        )
        result = self.use_case.execute(
            owner_id=1, filters=ListTransactionsFilters(account_id=10)
        )
        self.assertTrue(result.is_success)
        self.assertEqual(len(result.value), 1)
        self.assertEqual(result.value[0].account_id, 10)

    def test_filters_by_kind(self) -> None:
        self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        self.repo.seed(
            owner_id=1, account_id=10, kind="expense",
            amount=Decimal("50"), date=date(2026, 1, 2),
        )
        result = self.use_case.execute(
            owner_id=1, filters=ListTransactionsFilters(kind="income")
        )
        self.assertTrue(result.is_success)
        self.assertEqual(len(result.value), 1)
        self.assertEqual(result.value[0].kind, "income")

    def test_filters_by_date_range(self) -> None:
        self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("200"), date=date(2026, 2, 1),
        )
        self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("300"), date=date(2026, 3, 1),
        )
        result = self.use_case.execute(
            owner_id=1,
            filters=ListTransactionsFilters(date_from="2026-01-15", date_to="2026-02-15"),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(len(result.value), 1)
        self.assertEqual(result.value[0].amount, "200.00")

    def test_filters_by_category(self) -> None:
        self.repo.seed(
            owner_id=1, account_id=10, kind="expense",
            amount=Decimal("100"), date=date(2026, 1, 1), category_id=5,
        )
        self.repo.seed(
            owner_id=1, account_id=10, kind="expense",
            amount=Decimal("200"), date=date(2026, 1, 2), category_id=6,
        )
        result = self.use_case.execute(
            owner_id=1, filters=ListTransactionsFilters(category_id=5)
        )
        self.assertTrue(result.is_success)
        self.assertEqual(len(result.value), 1)
        self.assertEqual(result.value[0].category_id, 5)

    def test_filters_transactions_without_category(self) -> None:
        self.repo.seed(
            owner_id=1, account_id=10, kind="expense",
            amount=Decimal("100"), date=date(2026, 1, 1), category_id=5,
        )
        self.repo.seed(
            owner_id=1, account_id=10, kind="expense",
            amount=Decimal("200"), date=date(2026, 1, 2),
        )
        self.repo.seed(
            owner_id=1, account_id=10, kind="expense",
            amount=Decimal("300"), date=date(2026, 1, 3),
        )
        result = self.use_case.execute(
            owner_id=1, filters=ListTransactionsFilters(category_id_isnull=True)
        )
        self.assertTrue(result.is_success)
        self.assertEqual(len(result.value), 2)
        for tx in result.value:
            self.assertIsNone(tx.category_id)

    def test_orders_by_date_desc(self) -> None:
        self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("200"), date=date(2026, 3, 1),
        )
        self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("300"), date=date(2026, 2, 1),
        )
        result = self.use_case.execute(owner_id=1)
        self.assertTrue(result.is_success)
        dates = [t.date for t in result.value]
        self.assertEqual(dates, ["2026-03-01", "2026-02-01", "2026-01-01"])