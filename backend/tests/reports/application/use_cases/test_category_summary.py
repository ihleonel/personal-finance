"""Unit tests for GetCategorySummaryUseCase."""

from __future__ import annotations

import unittest
import uuid
from datetime import date
from decimal import Decimal

from django.utils import translation

from modules.reports.application.dtos import CategorySummaryInput
from modules.reports.application.use_cases.get_category_summary import (
    GetCategorySummaryUseCase,
)

from tests.fakes import (
    InMemoryAccountRepository,
    InMemoryCategoryRepository,
    InMemoryTransactionRepository,
)


class TestGetCategorySummaryUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryTransactionRepository()
        self.category_repo = InMemoryCategoryRepository()
        self.use_case = GetCategorySummaryUseCase(
            repository=self.repo,
            category_repository=self.category_repo,
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def _today(self) -> date:
        return date(2026, 6, 15)

    def test_builds_rows_for_active_categories_and_uncategorized(self) -> None:
        cat_food = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        cat_salary = self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        # July 2026 transactions (current month, partial column)
        self.repo.seed(owner_id=1, account_id=10, kind="income",
                       amount=Decimal("1000"), date=date(2026, 7, 5),
                       category_id=cat_salary.id)
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("200"), date=date(2026, 7, 8),
                       category_id=cat_food.id)
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("50"), date=date(2026, 7, 9),
                       category_id=None)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3)
        )
        self.assertTrue(result.is_success)
        rows = result.value.rows
        # Income block first
        self.assertEqual(rows[0].name, "Sueldo")
        self.assertEqual(rows[0].kind, "income")
        self.assertFalse(rows[0].is_uncategorized)
        # Expense block after
        expense_rows = [r for r in rows if r.kind == "expense"]
        self.assertEqual(expense_rows[0].name, "Comida")
        self.assertEqual(expense_rows[1].name, "Sin categoría")
        self.assertTrue(expense_rows[1].is_uncategorized)

    def test_rows_ordered_income_then_expense_alphabetical(self) -> None:
        self.category_repo.seed(owner_id=1, name="Zeta", kind="expense")
        self.category_repo.seed(owner_id=1, name="Alfa", kind="expense")
        self.category_repo.seed(owner_id=1, name="Beta", kind="income")
        self.category_repo.seed(owner_id=1, name="Alfa", kind="income")

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=1)
        )
        self.assertTrue(result.is_success)
        rows = result.value.rows
        names = [r.name for r in rows]
        self.assertEqual(names, ["Alfa", "Beta", "Alfa", "Zeta"])

    def test_all_categories_shown_even_without_movements(self) -> None:
        self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        # No transactions at all
        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3)
        )
        self.assertTrue(result.is_success)
        rows = result.value.rows
        self.assertEqual(len(rows), 2)
        for r in rows:
            self.assertTrue(all(a == "0.00" for a in r.amounts))
        # No uncategorized rows when no movement
        self.assertFalse(any(r.is_uncategorized for r in rows))

    def test_uncategorized_row_only_when_has_movements(self) -> None:
        self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        # Only income uncategorized, no expense uncategorized
        self.repo.seed(owner_id=1, account_id=10, kind="income",
                       amount=Decimal("100"), date=date(2026, 7, 1),
                       category_id=None)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=1)
        )
        rows = result.value.rows
        uncategorized = [r for r in rows if r.is_uncategorized]
        self.assertEqual(len(uncategorized), 1)
        self.assertEqual(uncategorized[0].kind, "income")

    def test_excludes_transfer_transactions(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("100"), date=date(2026, 7, 1),
                       category_id=cat.id,
                       transfer_group_id=uuid.uuid4())
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("200"), date=date(2026, 7, 2),
                       category_id=cat.id)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=1)
        )
        rows = result.value.rows
        food = [r for r in rows if r.name == "Comida"][0]
        # Only the non-transfer tx counts; current period col is last
        self.assertEqual(food.amounts[-1], "200.00")

    def test_account_filter_only_sums_that_account(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("100"), date=date(2026, 7, 1),
                       category_id=cat.id)
        self.repo.seed(owner_id=1, account_id=20, kind="expense",
                       amount=Decimal("200"), date=date(2026, 7, 2),
                       category_id=cat.id)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=1,
                                  account_id=10)
        )
        rows = result.value.rows
        food = [r for r in rows if r.name == "Comida"][0]
        self.assertEqual(food.amounts[-1], "100.00")

    def test_includes_current_period_partial_column(self) -> None:
        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3)
        )
        cols = result.value.columns
        self.assertEqual(len(cols), 4)  # 3 complete + 1 partial
        self.assertFalse(cols[0].is_partial)
        self.assertTrue(cols[-1].is_partial)
        self.assertGreater(cols[-1].days_total, 0)
        self.assertGreater(cols[-1].days_elapsed, 0)

    def test_no_transactions_all_zero(self) -> None:
        self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=2)
        )
        self.assertTrue(result.is_success)
        for r in result.value.rows:
            self.assertTrue(all(a == "0.00" for a in r.amounts))

    def test_weekly_keys_and_labels(self) -> None:
        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="week", periods_count=2)
        )
        cols = result.value.columns
        # 2 complete + 1 partial
        self.assertEqual(len(cols), 3)
        for c in cols[:-1]:
            self.assertIn("-W", c.key)

    def test_yearly_keys_and_labels(self) -> None:
        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="year", periods_count=2)
        )
        cols = result.value.columns
        for c in cols[:-1]:
            self.assertNotIn("-", c.key)

    def test_invalid_period(self) -> None:
        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="daily", periods_count=1)
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "reports.period.invalid")

    def test_periods_count_out_of_range(self) -> None:
        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=0)
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "reports.periods_count.invalid")

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=13)
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "reports.periods_count.invalid")

    def test_only_owner_transactions_counted(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("100"), date=date(2026, 7, 1),
                       category_id=cat.id)
        self.repo.seed(owner_id=2, account_id=20, kind="expense",
                       amount=Decimal("999"), date=date(2026, 7, 2),
                       category_id=None)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=1)
        )
        rows = result.value.rows
        food = [r for r in rows if r.name == "Comida"][0]
        self.assertEqual(food.amounts[-1], "100.00")
        # Other owner's uncategorized expense should not appear
        self.assertFalse(
            any(r.is_uncategorized and r.kind == "expense" for r in rows)
        )

    def test_inactive_categories_shown_as_rows(self) -> None:
        cat = self.category_repo.seed(
            owner_id=1, name="Vieja", kind="expense", is_active=False
        )
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("100"), date=date(2026, 7, 1),
                       category_id=cat.id)
        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=1)
        )
        rows = result.value.rows
        old = [r for r in rows if r.name == "Vieja"][0]
        self.assertFalse(old.is_active)
        self.assertEqual(old.amounts[-1], "100.00")

    def test_totals_net_per_column(self) -> None:
        cat_food = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        cat_salary = self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        # Current period (partial, last column): 1000 income - 200 expense - 50 uncategorized
        self.repo.seed(owner_id=1, account_id=10, kind="income",
                       amount=Decimal("1000"), date=date(2026, 7, 5),
                       category_id=cat_salary.id)
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("200"), date=date(2026, 7, 8),
                       category_id=cat_food.id)
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("50"), date=date(2026, 7, 9),
                       category_id=None)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3)
        )
        self.assertTrue(result.is_success)
        totals = result.value.totals
        n_cols = len(result.value.columns)
        self.assertEqual(len(totals.amounts), n_cols)
        # Last column = current period: 1000 - 200 - 50 = 750
        self.assertEqual(totals.amounts[-1], "750.00")
        # Previous columns all zero
        for amt in totals.amounts[:-1]:
            self.assertEqual(amt, "0.00")

    def test_totals_equal_income_minus_expense(self) -> None:
        cat_food = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        cat_salary = self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        self.repo.seed(owner_id=1, account_id=10, kind="income",
                       amount=Decimal("1000"), date=date(2026, 7, 5),
                       category_id=cat_salary.id)
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("200"), date=date(2026, 7, 8),
                       category_id=cat_food.id)
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("50"), date=date(2026, 7, 9),
                       category_id=None)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3)
        )
        rows = result.value.rows
        totals = result.value.totals
        for i, total in enumerate(totals.amounts):
            income_sum = sum(
                Decimal(r.amounts[i]) for r in rows if r.kind == "income"
            )
            expense_sum = sum(
                Decimal(r.amounts[i]) for r in rows if r.kind == "expense"
            )
            self.assertEqual(Decimal(total), income_sum - expense_sum)

    def test_totals_negative_when_expense_exceeds_income(self) -> None:
        cat_food = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("500"), date=date(2026, 7, 8),
                       category_id=cat_food.id)
        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=1)
        )
        # Only expense: -500
        self.assertEqual(result.value.totals.amounts[-1], "-500.00")

    def test_totals_zero_when_no_transactions(self) -> None:
        self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=2)
        )
        self.assertTrue(result.is_success)
        for amt in result.value.totals.amounts:
            self.assertEqual(amt, "0.00")

    def test_totals_excludes_transfers(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("100"), date=date(2026, 7, 1),
                       category_id=cat.id,
                       transfer_group_id=uuid.uuid4())
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("200"), date=date(2026, 7, 2),
                       category_id=cat.id)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=1)
        )
        # Only the non-transfer tx counts: -200 (expense)
        self.assertEqual(result.value.totals.amounts[-1], "-200.00")

    def test_accumulated_running_balance_includes_previous_periods(self) -> None:
        cat_food = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        cat_salary = self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        # Transactions before the window (months_count=3 -> window starts Apr 2026)
        # March 2026: 500 income - 100 expense = +400 initial balance
        self.repo.seed(owner_id=1, account_id=10, kind="income",
                       amount=Decimal("500"), date=date(2026, 3, 5),
                       category_id=cat_salary.id)
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("100"), date=date(2026, 3, 8),
                       category_id=cat_food.id)
        # Current period (partial, last column = Jul 2026): 1000 - 200 = +800
        self.repo.seed(owner_id=1, account_id=10, kind="income",
                       amount=Decimal("1000"), date=date(2026, 7, 5),
                       category_id=cat_salary.id)
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("200"), date=date(2026, 7, 8),
                       category_id=cat_food.id)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3)
        )
        self.assertTrue(result.is_success)
        totals = result.value.totals
        n_cols = len(result.value.columns)
        self.assertEqual(len(totals.accumulated), n_cols)
        # Apr, May, Jun -> 400 (initial), Jul -> 400 + 800 = 1200
        self.assertEqual(totals.accumulated[-1], "1200.00")
        # First columns carry the initial balance (no movements in Apr/May/Jun)
        self.assertEqual(totals.accumulated[0], "400.00")
        self.assertEqual(totals.accumulated[1], "400.00")

    def test_accumulated_reflects_per_period_net(self) -> None:
        cat_food = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        cat_salary = self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        # Window: Apr-Jul 2026 (periods_count=3 month)
        # Apr 2026 (complete, first col): +300 income
        self.repo.seed(owner_id=1, account_id=10, kind="income",
                       amount=Decimal("300"), date=date(2026, 4, 10),
                       category_id=cat_salary.id)
        # May 2026 (complete, second col): -150 expense
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("150"), date=date(2026, 5, 10),
                       category_id=cat_food.id)
        # Jul 2026 (partial, last col): +1000 income
        self.repo.seed(owner_id=1, account_id=10, kind="income",
                       amount=Decimal("1000"), date=date(2026, 7, 5),
                       category_id=cat_salary.id)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3)
        )
        totals = result.value.totals
        # No previous transactions -> initial balance = 0
        # Apr: 0 + 300 = 300
        self.assertEqual(totals.accumulated[0], "300.00")
        # May: 300 - 150 = 150
        self.assertEqual(totals.accumulated[1], "150.00")
        # Jun: 150 + 0 = 150
        self.assertEqual(totals.accumulated[2], "150.00")
        # Jul: 150 + 1000 = 1150
        self.assertEqual(totals.accumulated[-1], "1150.00")

    def test_accumulated_excludes_transfers(self) -> None:
        cat = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        # Previous period transfer (excluded) + real expense
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("1000"), date=date(2026, 3, 1),
                       category_id=cat.id,
                       transfer_group_id=uuid.uuid4())
        self.repo.seed(owner_id=1, account_id=10, kind="expense",
                       amount=Decimal("200"), date=date(2026, 3, 2),
                       category_id=cat.id)
        # Current period: +500 income
        cat_salary = self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        self.repo.seed(owner_id=1, account_id=10, kind="income",
                       amount=Decimal("500"), date=date(2026, 7, 5),
                       category_id=cat_salary.id)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3)
        )
        totals = result.value.totals
        # Initial balance: -200 (transfer excluded)
        # Jul: -200 + 500 = 300
        self.assertEqual(totals.accumulated[0], "-200.00")
        self.assertEqual(totals.accumulated[-1], "300.00")

    def test_accumulated_account_filter_isolated(self) -> None:
        cat_salary = self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        # Account 10 previous period: +1000
        self.repo.seed(owner_id=1, account_id=10, kind="income",
                       amount=Decimal("1000"), date=date(2026, 3, 5),
                       category_id=cat_salary.id)
        # Account 20 previous period: +9999 (should be excluded by filter)
        self.repo.seed(owner_id=1, account_id=20, kind="income",
                       amount=Decimal("9999"), date=date(2026, 3, 5),
                       category_id=cat_salary.id)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3,
                                  account_id=10)
        )
        totals = result.value.totals
        # Initial balance: 1000 (account 20 excluded)
        # No movements in window -> all columns 1000
        for amt in totals.accumulated:
            self.assertEqual(amt, "1000.00")


class TestGetCategorySummaryAccumulatedWithInitialBalance(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryTransactionRepository()
        self.category_repo = InMemoryCategoryRepository()
        self.account_repo = InMemoryAccountRepository()
        self.use_case = GetCategorySummaryUseCase(
            repository=self.repo,
            category_repository=self.category_repo,
            account_repository=self.account_repo,
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_accumulated_includes_account_initial_balance(self) -> None:
        cat_salary = self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        cat_food = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        account = self.account_repo.seed(
            owner_id=1, name="Banco", initial_balance=Decimal("500.00")
        )
        # Previous period (March 2026): +400 net
        self.repo.seed(owner_id=1, account_id=account.id, kind="income",
                       amount=Decimal("500"), date=date(2026, 3, 5),
                       category_id=cat_salary.id)
        self.repo.seed(owner_id=1, account_id=account.id, kind="expense",
                       amount=Decimal("100"), date=date(2026, 3, 8),
                       category_id=cat_food.id)
        # Current period (Jul 2026): +800 net
        self.repo.seed(owner_id=1, account_id=account.id, kind="income",
                       amount=Decimal("1000"), date=date(2026, 7, 5),
                       category_id=cat_salary.id)
        self.repo.seed(owner_id=1, account_id=account.id, kind="expense",
                       amount=Decimal("200"), date=date(2026, 7, 8),
                       category_id=cat_food.id)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3,
                                 account_id=account.id)
        )
        self.assertTrue(result.is_success)
        totals = result.value.totals
        # initial_balance = 500 (account) + 400 (prior txs) = 900
        # first cols: 900 (no movements in Apr/May/Jun)
        # last col: 900 + 800 = 1700
        self.assertEqual(totals.accumulated[0], "900.00")
        self.assertEqual(totals.accumulated[-1], "1700.00")

    def test_accumulated_includes_initial_balance_without_account_id(self) -> None:
        cat_salary = self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        self.account_repo.seed(
            owner_id=1, name="Banco", initial_balance=Decimal("500.00")
        )
        # Previous period: +400
        self.repo.seed(owner_id=1, account_id=10, kind="income",
                       amount=Decimal("400"), date=date(2026, 3, 5),
                       category_id=cat_salary.id)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3)
        )
        self.assertTrue(result.is_success)
        totals = result.value.totals
        # No account_id -> sum initial_balance of all active accounts (500)
        # plus prior txs (400) = 900
        self.assertEqual(totals.accumulated[0], "900.00")

    def test_accumulated_ignores_initial_balance_when_account_repo_is_none(self) -> None:
        cat_salary = self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        account = self.account_repo.seed(
            owner_id=1, name="Banco", initial_balance=Decimal("500.00")
        )
        # Previous period: +400
        self.repo.seed(owner_id=1, account_id=account.id, kind="income",
                       amount=Decimal("400"), date=date(2026, 3, 5),
                       category_id=cat_salary.id)

        use_case_no_account_repo = GetCategorySummaryUseCase(
            repository=self.repo,
            category_repository=self.category_repo,
        )
        result = use_case_no_account_repo.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3,
                                 account_id=account.id)
        )
        self.assertTrue(result.is_success)
        totals = result.value.totals
        # account_repository is None -> only txs = 400
        self.assertEqual(totals.accumulated[0], "400.00")

    def test_accumulated_initial_balance_from_other_owner_ignored(self) -> None:
        cat_salary = self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        # Account owned by user 2
        account = self.account_repo.seed(
            owner_id=2, name="Ajena", initial_balance=Decimal("500.00")
        )
        # Previous period txs for owner 1 on account 10
        self.repo.seed(owner_id=1, account_id=10, kind="income",
                       amount=Decimal("400"), date=date(2026, 3, 5),
                       category_id=cat_salary.id)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3,
                                 account_id=account.id)
        )
        self.assertTrue(result.is_success)
        totals = result.value.totals
        # Account belongs to owner 2 -> initial_balance not added; only txs
        # for owner 1 with that account_id (none) -> 0
        self.assertEqual(totals.accumulated[0], "0.00")

    def test_accumulated_sums_all_active_accounts_without_account_id(self) -> None:
        cat_salary = self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        # Two active accounts with initial_balance 500 + 300 = 800
        self.account_repo.seed(
            owner_id=1, name="Efectivo", initial_balance=Decimal("500.00")
        )
        self.account_repo.seed(
            owner_id=1, name="Banco", initial_balance=Decimal("300.00")
        )
        # Previous period tx (March 2026): +400 net
        self.repo.seed(owner_id=1, account_id=10, kind="income",
                       amount=Decimal("400"), date=date(2026, 3, 5),
                       category_id=cat_salary.id)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3)
        )
        self.assertTrue(result.is_success)
        totals = result.value.totals
        # initial = 800 (sum of active accounts) + 400 (prior tx) = 1200
        self.assertEqual(totals.accumulated[0], "1200.00")
        self.assertEqual(totals.accumulated[-1], "1200.00")

    def test_accumulated_excludes_inactive_accounts_without_account_id(self) -> None:
        cat_salary = self.category_repo.seed(owner_id=1, name="Sueldo", kind="income")
        active = self.account_repo.seed(
            owner_id=1, name="Efectivo", initial_balance=Decimal("500.00")
        )
        inactive = self.account_repo.seed(
            owner_id=1, name="Vieja", initial_balance=Decimal("9999.00")
        )
        self.account_repo.deactivate(inactive.id)
        # Previous period tx: +400
        self.repo.seed(owner_id=1, account_id=active.id, kind="income",
                       amount=Decimal("400"), date=date(2026, 3, 5),
                       category_id=cat_salary.id)

        result = self.use_case.execute(
            CategorySummaryInput(owner_id=1, period="month", periods_count=3)
        )
        self.assertTrue(result.is_success)
        totals = result.value.totals
        # initial = 500 (only active) + 400 = 900 (inactive 9999 excluded)
        self.assertEqual(totals.accumulated[0], "900.00")