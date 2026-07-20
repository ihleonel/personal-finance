"""Unit tests for GetAccountBalanceUseCase."""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from django.utils import translation

from modules.accounts.application.use_cases.get_account_balance import (
    GetAccountBalanceUseCase,
)

from tests.fakes import InMemoryAccountRepository, InMemoryTransactionRepository


class TestGetAccountBalanceUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.tx_repo = InMemoryTransactionRepository()
        self.account_repo = InMemoryAccountRepository()
        self.use_case = GetAccountBalanceUseCase(
            repository=self.tx_repo,
            account_repository=self.account_repo,
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_balance_is_initial_when_no_transactions(self) -> None:
        account = self.account_repo.seed(
            owner_id=1, name="Efectivo", initial_balance=Decimal("500.00")
        )
        result = self.use_case.execute(owner_id=1, account_id=account.id)
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.initial_balance, "500.00")
        self.assertEqual(out.current_balance, "500.00")
        self.assertIsNone(out.as_of)

    def test_balance_sums_income_and_subtracts_expense(self) -> None:
        account = self.account_repo.seed(
            owner_id=1, name="Banco", initial_balance=Decimal("1000.00")
        )
        self.tx_repo.seed(
            owner_id=1, account_id=account.id, kind="income",
            amount=Decimal("500"), date=date(2026, 6, 1), description="x",
        )
        self.tx_repo.seed(
            owner_id=1, account_id=account.id, kind="expense",
            amount=Decimal("300"), date=date(2026, 6, 2), description="y",
        )
        result = self.use_case.execute(owner_id=1, account_id=account.id)
        self.assertTrue(result.is_success)
        # 1000 + 500 - 300 = 1200
        self.assertEqual(result.value.current_balance, "1200.00")

    def test_balance_includes_transfers(self) -> None:
        source = self.account_repo.seed(
            owner_id=1, name="Efectivo", initial_balance=Decimal("1000.00")
        )
        dest = self.account_repo.seed(
            owner_id=1, name="Banco", initial_balance=Decimal("0.00")
        )
        self.tx_repo.seed(
            owner_id=1, account_id=source.id, kind="expense",
            amount=Decimal("400"), date=date(2026, 6, 1), description="transfer out",
        )
        self.tx_repo.seed(
            owner_id=1, account_id=dest.id, kind="income",
            amount=Decimal("400"), date=date(2026, 6, 1), description="transfer in",
        )
        result_source = self.use_case.execute(owner_id=1, account_id=source.id)
        result_dest = self.use_case.execute(owner_id=1, account_id=dest.id)
        self.assertTrue(result_source.is_success)
        self.assertTrue(result_dest.is_success)
        # Source: 1000 - 400 = 600
        self.assertEqual(result_source.value.current_balance, "600.00")
        # Dest: 0 + 400 = 400
        self.assertEqual(result_dest.value.current_balance, "400.00")

    def test_balance_respects_date_to(self) -> None:
        account = self.account_repo.seed(
            owner_id=1, name="Banco", initial_balance=Decimal("1000.00")
        )
        self.tx_repo.seed(
            owner_id=1, account_id=account.id, kind="income",
            amount=Decimal("500"), date=date(2026, 6, 1), description="x",
        )
        self.tx_repo.seed(
            owner_id=1, account_id=account.id, kind="income",
            amount=Decimal("500"), date=date(2026, 7, 1), description="y",
        )
        result = self.use_case.execute(
            owner_id=1, account_id=account.id, date_to=date(2026, 6, 15)
        )
        self.assertTrue(result.is_success)
        # Only the June income counts: 1000 + 500 = 1500
        self.assertEqual(result.value.current_balance, "1500.00")
        self.assertEqual(result.value.as_of, "2026-06-15")

    def test_balance_fails_for_other_owner_account(self) -> None:
        account = self.account_repo.seed(
            owner_id=2, name="Ajena", initial_balance=Decimal("1000.00")
        )
        result = self.use_case.execute(owner_id=1, account_id=account.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "accounts.account.not_found")

    def test_balance_fails_for_missing_account(self) -> None:
        result = self.use_case.execute(owner_id=1, account_id=99999)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "accounts.account.not_found")


if __name__ == "__main__":
    unittest.main()