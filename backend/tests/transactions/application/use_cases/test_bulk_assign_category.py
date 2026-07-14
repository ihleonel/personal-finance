"""Unit tests for BulkAssignCategoryUseCase."""

from __future__ import annotations

import unittest
import uuid
from datetime import date
from decimal import Decimal

from django.utils import translation

from modules.transactions.application.dtos import BulkAssignCategoryInput
from modules.transactions.application.use_cases.bulk_assign_category import (
    BulkAssignCategoryUseCase,
)

from tests.fakes import (
    InMemoryCategoryRepository,
    InMemoryTransactionRepository,
)


class TestBulkAssignCategoryUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryTransactionRepository()
        self.category_repo = InMemoryCategoryRepository()
        self.use_case = BulkAssignCategoryUseCase(
            repository=self.repo,
            category_repository=self.category_repo,
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_assigns_category_to_multiple_transactions(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        t1 = self.repo.seed(owner_id=1, account_id=10, kind="expense",
                             amount=Decimal("100"), date=date(2026, 1, 1))
        t2 = self.repo.seed(owner_id=1, account_id=10, kind="expense",
                             amount=Decimal("50"), date=date(2026, 1, 2))
        result = self.use_case.execute(
            BulkAssignCategoryInput(
                owner_id=1, transaction_ids=[t1.id, t2.id], category_id=cat.id,
            )
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.updated_count, 2)
        self.assertEqual(self.repo.find_by_id(t1.id).category_id, cat.id)
        self.assertEqual(self.repo.find_by_id(t2.id).category_id, cat.id)

    def test_clears_category_when_category_id_is_none(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        t1 = self.repo.seed(owner_id=1, account_id=10, kind="expense",
                             amount=Decimal("100"), date=date(2026, 1, 1),
                             category_id=cat.id)
        t2 = self.repo.seed(owner_id=1, account_id=10, kind="expense",
                             amount=Decimal("50"), date=date(2026, 1, 2),
                             category_id=cat.id)
        result = self.use_case.execute(
            BulkAssignCategoryInput(
                owner_id=1, transaction_ids=[t1.id, t2.id], category_id=None,
            )
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.updated_count, 2)
        self.assertIsNone(self.repo.find_by_id(t1.id).category_id)
        self.assertIsNone(self.repo.find_by_id(t2.id).category_id)

    def test_fails_when_empty_transaction_ids(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        result = self.use_case.execute(
            BulkAssignCategoryInput(
                owner_id=1, transaction_ids=[], category_id=cat.id,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.bulk.empty")

    def test_fails_when_category_not_owned(self) -> None:
        result = self.use_case.execute(
            BulkAssignCategoryInput(
                owner_id=1, transaction_ids=[1], category_id=9999,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.category.not_found")

    def test_skips_transactions_of_other_kinds(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        t1 = self.repo.seed(owner_id=1, account_id=10, kind="expense",
                             amount=Decimal("100"), date=date(2026, 1, 1))
        t2 = self.repo.seed(owner_id=1, account_id=10, kind="income",
                             amount=Decimal("200"), date=date(2026, 1, 2))
        result = self.use_case.execute(
            BulkAssignCategoryInput(
                owner_id=1, transaction_ids=[t1.id, t2.id], category_id=cat.id,
            )
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.updated_count, 1)
        self.assertEqual(result.value.skipped_kinds, [t2.id])
        self.assertEqual(self.repo.find_by_id(t1.id).category_id, cat.id)
        self.assertIsNone(self.repo.find_by_id(t2.id).category_id)

    def test_skips_transfers(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        t1 = self.repo.seed(owner_id=1, account_id=10, kind="expense",
                             amount=Decimal("100"), date=date(2026, 1, 1))
        t2 = self.repo.seed(owner_id=1, account_id=10, kind="expense",
                             amount=Decimal("50"), date=date(2026, 1, 2),
                             transfer_group_id=uuid.uuid4())
        result = self.use_case.execute(
            BulkAssignCategoryInput(
                owner_id=1, transaction_ids=[t1.id, t2.id], category_id=cat.id,
            )
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.updated_count, 1)
        self.assertEqual(result.value.skipped_transfers, [t2.id])

    def test_fails_when_all_skipped_due_to_kind_mismatch(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        t1 = self.repo.seed(owner_id=1, account_id=10, kind="expense",
                             amount=Decimal("100"), date=date(2026, 1, 1))
        result = self.use_case.execute(
            BulkAssignCategoryInput(
                owner_id=1, transaction_ids=[t1.id], category_id=cat.id,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.bulk.kind_mismatch")

    def test_fails_when_all_are_transfers(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        t1 = self.repo.seed(owner_id=1, account_id=10, kind="expense",
                             amount=Decimal("100"), date=date(2026, 1, 1),
                             transfer_group_id=uuid.uuid4())
        result = self.use_case.execute(
            BulkAssignCategoryInput(
                owner_id=1, transaction_ids=[t1.id], category_id=cat.id,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.bulk.all_transfers")

    def test_skips_transactions_of_other_owner(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        t1 = self.repo.seed(owner_id=1, account_id=10, kind="expense",
                             amount=Decimal("100"), date=date(2026, 1, 1))
        t2 = self.repo.seed(owner_id=2, account_id=20, kind="expense",
                             amount=Decimal("50"), date=date(2026, 1, 2))
        result = self.use_case.execute(
            BulkAssignCategoryInput(
                owner_id=1, transaction_ids=[t1.id, t2.id], category_id=cat.id,
            )
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.updated_count, 1)
        self.assertIn(t2.id, result.value.skipped_ids)