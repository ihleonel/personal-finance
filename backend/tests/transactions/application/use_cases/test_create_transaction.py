"""Unit tests for CreateTransactionUseCase."""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from django.utils import translation

from modules.accounts.domain.entities import Account
from modules.categories.domain.entities import Category
from modules.transactions.application.dtos import CreateTransactionInput
from modules.transactions.application.use_cases.create_transaction import (
    CreateTransactionUseCase,
)

from tests.fakes import (
    InMemoryAccountRepository,
    InMemoryCategoryRepository,
    InMemoryTransactionRepository,
)


class TestCreateTransactionUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.tx_repo = InMemoryTransactionRepository()
        self.account_repo = InMemoryAccountRepository()
        self.category_repo = InMemoryCategoryRepository()
        self.use_case = CreateTransactionUseCase(
            repository=self.tx_repo,
            account_repository=self.account_repo,
            category_repository=self.category_repo,
        )
        self.account = self.account_repo.seed(
            owner_id=1, name="Efectivo", currency="ARS"
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_creates_income_transaction(self) -> None:
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=self.account.id,
                kind="income",
                amount="1000.00",
                date="2026-01-15",
                description="Salario",
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.owner_id, 1)
        self.assertEqual(out.account_id, self.account.id)
        self.assertEqual(out.kind, "income")
        self.assertEqual(out.amount, "1000.00")
        self.assertEqual(out.date, "2026-01-15")
        self.assertEqual(out.description, "Salario")
        self.assertIsNone(out.category_id)

    def test_creates_expense_transaction(self) -> None:
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=self.account.id,
                kind="expense",
                amount="500.50",
                date="2026-01-20",
            )
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.kind, "expense")
        self.assertEqual(result.value.amount, "500.50")
        self.assertEqual(result.value.description, "")

    def test_creates_with_category(self) -> None:
        category = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=self.account.id,
                kind="expense",
                amount="200.00",
                date="2026-01-20",
                category_id=category.id,
            )
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.category_id, category.id)

    def test_fails_when_kind_invalid(self) -> None:
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=self.account.id,
                kind="transfer",
                amount="100.00",
                date="2026-01-20",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "kind")
        self.assertEqual(result.errors[0].code, "transactions.kind.invalid")
        self.assertEqual(result.errors[0].message, "El tipo de transacción no es válido.")

    def test_fails_when_amount_not_numeric(self) -> None:
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=self.account.id,
                kind="income",
                amount="not-a-number",
                date="2026-01-20",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "amount")
        self.assertEqual(result.errors[0].code, "transactions.amount.invalid")

    def test_fails_when_amount_zero_or_negative(self) -> None:
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=self.account.id,
                kind="income",
                amount="-100.00",
                date="2026-01-20",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "amount")
        self.assertEqual(result.errors[0].code, "transactions.amount.invalid")

    def test_fails_when_date_in_future(self) -> None:
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=self.account.id,
                kind="income",
                amount="100.00",
                date="2999-12-31",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "date")
        self.assertEqual(result.errors[0].code, "transactions.date.invalid")

    def test_fails_when_date_invalid_format(self) -> None:
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=self.account.id,
                kind="income",
                amount="100.00",
                date="not-a-date",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "date")
        self.assertEqual(result.errors[0].code, "transactions.date.invalid")

    def test_fails_when_account_not_found(self) -> None:
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=9999,
                kind="income",
                amount="100.00",
                date="2026-01-20",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "account")
        self.assertEqual(result.errors[0].code, "transactions.account.not_found")

    def test_fails_when_account_belongs_to_other_user(self) -> None:
        other_account = self.account_repo.seed(owner_id=2, name="Ajena")
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=other_account.id,
                kind="income",
                amount="100.00",
                date="2026-01-20",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.account.not_found")

    def test_fails_when_category_not_found(self) -> None:
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=self.account.id,
                kind="expense",
                amount="100.00",
                date="2026-01-20",
                category_id=9999,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "category")
        self.assertEqual(result.errors[0].code, "transactions.category.not_found")

    def test_fails_when_category_belongs_to_other_user(self) -> None:
        other_category = self.category_repo.seed(owner_id=2, name="Ajena")
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=self.account.id,
                kind="expense",
                amount="100.00",
                date="2026-01-20",
                category_id=other_category.id,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.category.not_found")

    def test_fails_when_description_too_long(self) -> None:
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=self.account.id,
                kind="income",
                amount="100.00",
                date="2026-01-20",
                description="x" * 256,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "description")
        self.assertEqual(result.errors[0].code, "transactions.description.max_length")

    def test_does_not_persist_when_validation_fails(self) -> None:
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=self.account.id,
                kind="invalid",
                amount="100.00",
                date="2026-01-20",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(self.tx_repo.list_by_owner(1), [])

    def test_accumulates_multiple_errors(self) -> None:
        result = self.use_case.execute(
            CreateTransactionInput(
                owner_id=1,
                account_id=9999,
                kind="invalid",
                amount="not-a-number",
                date="not-a-date",
            )
        )
        self.assertFalse(result.is_success)
        fields = [e.field for e in result.errors]
        self.assertIn("kind", fields)
        self.assertIn("amount", fields)
        self.assertIn("date", fields)
        self.assertIn("account", fields)
        self.assertEqual(len(result.errors), 4)