"""Unit tests for AssignCategoryByFiltersUseCase."""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from django.utils import translation

from modules.transactions.application.dtos import (
    AssignCategoryByFiltersInput,
    ListTransactionsFilters,
)
from modules.transactions.application.use_cases.assign_category_by_filters import (
    AssignCategoryByFiltersUseCase,
)

from tests.fakes import (
    InMemoryCategoryRepository,
    InMemoryTransactionRepository,
)


class TestAssignCategoryByFiltersUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryTransactionRepository()
        self.category_repo = InMemoryCategoryRepository()
        self.use_case = AssignCategoryByFiltersUseCase(
            repository=self.repo,
            category_repository=self.category_repo,
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_assigns_to_all_without_category(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        t1 = self.repo.seed(owner_id=1, account_id=10, kind="expense",
                            amount=Decimal("100"), date=date(2026, 1, 1))
        t2 = self.repo.seed(owner_id=1, account_id=10, kind="expense",
                            amount=Decimal("50"), date=date(2026, 1, 2))
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("30"), date=date(2026, 1, 3),
                       category_id=cat.id)
        result = self.use_case.execute(
            AssignCategoryByFiltersInput(
                owner_id=1,
                filters=ListTransactionsFilters(category_id_isnull=True),
                category_id=cat.id,
            )
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.updated_count, 2)
        self.assertEqual(self.repo.find_by_id(t1.id).category_id, cat.id)
        self.assertEqual(self.repo.find_by_id(t2.id).category_id, cat.id)

    def test_assigns_filtered_by_account_and_kind(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        t1 = self.repo.seed(owner_id=1, account_id=10, kind="expense",
                            amount=Decimal("100"), date=date(2026, 1, 1))
        self.repo.seed(owner_id=1, account_id=20, kind="expense",
                       amount=Decimal("50"), date=date(2026, 1, 2))
        self.repo.seed(owner_id=1, account_id=10, kind="income",
                       amount=Decimal("200"), date=date(2026, 1, 3))
        result = self.use_case.execute(
            AssignCategoryByFiltersInput(
                owner_id=1,
                filters=ListTransactionsFilters(account_id=10, kind="expense"),
                category_id=cat.id,
            )
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.updated_count, 1)
        self.assertEqual(self.repo.find_by_id(t1.id).category_id, cat.id)

    def test_excludes_transfers(self) -> None:
        import uuid as _uuid
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("100"), date=date(2026, 1, 1),
                       transfer_group_id=_uuid.uuid4())
        result = self.use_case.execute(
            AssignCategoryByFiltersInput(
                owner_id=1,
                filters=ListTransactionsFilters(account_id=10, kind="expense"),
                category_id=cat.id,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.bulk.no_valid_transactions")

    def test_clears_category_with_none(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        t1 = self.repo.seed(owner_id=1, account_id=10, kind="expense",
                            amount=Decimal("100"), date=date(2026, 1, 1),
                            category_id=cat.id)
        result = self.use_case.execute(
            AssignCategoryByFiltersInput(
                owner_id=1,
                filters=ListTransactionsFilters(account_id=10, kind="expense"),
                category_id=None,
            )
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.updated_count, 1)
        self.assertIsNone(self.repo.find_by_id(t1.id).category_id)

    def test_fails_when_category_not_owned(self) -> None:
        result = self.use_case.execute(
            AssignCategoryByFiltersInput(
                owner_id=1,
                filters=ListTransactionsFilters(),
                category_id=9999,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.category.not_found")

    def test_fails_when_no_matches(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        result = self.use_case.execute(
            AssignCategoryByFiltersInput(
                owner_id=1,
                filters=ListTransactionsFilters(account_id=999),
                category_id=cat.id,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.bulk.no_valid_transactions")