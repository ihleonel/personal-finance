"""Unit tests for UpdateTransactionUseCase."""

from __future__ import annotations

import unittest
import uuid
from datetime import date
from decimal import Decimal

from django.utils import translation

from modules.transactions.application.dtos import UpdateTransactionInput
from modules.transactions.application.use_cases.update_transaction import (
    UpdateTransactionUseCase,
)

from tests.fakes import (
    InMemoryCategoryRepository,
    InMemoryTransactionRepository,
)


class TestUpdateTransactionUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryTransactionRepository()
        self.category_repo = InMemoryCategoryRepository()
        self.use_case = UpdateTransactionUseCase(
            repository=self.repo,
            category_repository=self.category_repo,
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_updates_amount(self) -> None:
        tx = self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        result = self.use_case.execute(
            owner_id=1, transaction_id=tx.id,
            data=UpdateTransactionInput(amount="250.00"),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.amount, "250.00")

    def test_updates_date(self) -> None:
        tx = self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        result = self.use_case.execute(
            owner_id=1, transaction_id=tx.id,
            data=UpdateTransactionInput(date="2026-02-15"),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.date, "2026-02-15")

    def test_updates_description(self) -> None:
        tx = self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        result = self.use_case.execute(
            owner_id=1, transaction_id=tx.id,
            data=UpdateTransactionInput(description="Nuevo texto"),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.description, "Nuevo texto")

    def test_updates_category(self) -> None:
        category = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        tx = self.repo.seed(
            owner_id=1, account_id=10, kind="expense",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        result = self.use_case.execute(
            owner_id=1, transaction_id=tx.id,
            data=UpdateTransactionInput(category_id=category.id),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.category_id, category.id)

    def test_clears_category_when_category_id_is_none(self) -> None:
        category = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        tx = self.repo.seed(
            owner_id=1, account_id=10, kind="expense",
            amount=Decimal("100"), date=date(2026, 1, 1),
            category_id=category.id,
        )
        result = self.use_case.execute(
            owner_id=1, transaction_id=tx.id,
            data=UpdateTransactionInput(category_id=None),
        )
        self.assertTrue(result.is_success)
        self.assertIsNone(result.value.category_id)

    def test_does_not_change_category_when_field_not_sent(self) -> None:
        category = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        tx = self.repo.seed(
            owner_id=1, account_id=10, kind="expense",
            amount=Decimal("100"), date=date(2026, 1, 1),
            category_id=category.id,
        )
        result = self.use_case.execute(
            owner_id=1, transaction_id=tx.id,
            data=UpdateTransactionInput(amount="200.00"),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.category_id, category.id)

    def test_fails_when_transaction_not_found(self) -> None:
        result = self.use_case.execute(
            owner_id=1, transaction_id=9999,
            data=UpdateTransactionInput(amount="100.00"),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transaction.not_found")

    def test_fails_when_transaction_belongs_to_other_user(self) -> None:
        tx = self.repo.seed(
            owner_id=2, account_id=20, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        result = self.use_case.execute(
            owner_id=1, transaction_id=tx.id,
            data=UpdateTransactionInput(amount="100.00"),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transaction.not_found")

    def test_fails_when_empty_payload(self) -> None:
        tx = self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        result = self.use_case.execute(
            owner_id=1, transaction_id=tx.id,
            data=UpdateTransactionInput(),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transaction.empty_payload")

    def test_fails_when_amount_invalid(self) -> None:
        tx = self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        result = self.use_case.execute(
            owner_id=1, transaction_id=tx.id,
            data=UpdateTransactionInput(amount="not-a-number"),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "amount")
        self.assertEqual(result.errors[0].code, "transactions.amount.invalid")

    def test_fails_when_date_in_future(self) -> None:
        tx = self.repo.seed(
            owner_id=1, account_id=10, kind="income",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        result = self.use_case.execute(
            owner_id=1, transaction_id=tx.id,
            data=UpdateTransactionInput(date="2999-12-31"),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "date")
        self.assertEqual(result.errors[0].code, "transactions.date.invalid")

    def test_fails_when_category_not_owned(self) -> None:
        tx = self.repo.seed(
            owner_id=1, account_id=10, kind="expense",
            amount=Decimal("100"), date=date(2026, 1, 1),
        )
        result = self.use_case.execute(
            owner_id=1, transaction_id=tx.id,
            data=UpdateTransactionInput(category_id=9999),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "category")
        self.assertEqual(result.errors[0].code, "transactions.category.not_found")

    def test_fails_when_transaction_is_part_of_transfer(self) -> None:
        group_id = uuid.uuid4()
        tx = self.repo.seed(
            owner_id=1, account_id=10, kind="expense",
            amount=Decimal("100"), date=date(2026, 1, 1),
            transfer_group_id=group_id,
        )
        result = self.use_case.execute(
            owner_id=1, transaction_id=tx.id,
            data=UpdateTransactionInput(amount="200.00"),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transaction.is_transfer")