"""Unit tests for GetIncomeExpenseSummaryUseCase."""

from __future__ import annotations

import unittest
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from django.utils import translation

from modules.reports.application.dtos import IncomeExpenseSummaryInput
from modules.reports.application.use_cases.get_income_expense_summary import (
    GetIncomeExpenseSummaryUseCase,
)

from tests.fakes import (
    InMemoryAccountRepository,
    InMemoryCategoryRepository,
    InMemoryTransactionRepository,
)


class TestGetIncomeExpenseSummaryUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.tx_repo = InMemoryTransactionRepository()
        self.use_case = GetIncomeExpenseSummaryUseCase(repository=self.tx_repo)
        self.today = date.today()
        self.owner_id = 1
        self.account_a = 10
        self.account_b = 20

    def tearDown(self) -> None:
        translation.deactivate_all()

    def _month_start(self, d: date) -> date:
        return d.replace(day=1)

    def _months_ago_date(self, months_back: int, day: int = 15) -> date:
        idx = self.today.year * 12 + (self.today.month - 1) - months_back
        year, month = divmod(idx, 12)
        return date(year, month + 1, day)

    def _years_ago_date(self, years_back: int) -> date:
        return date(self.today.year - years_back, 6, 15)

    def _week_start(self, d: date) -> date:
        return d - timedelta(days=d.weekday())

    def _seed(self, tx_date: date, kind: str, amount: str, account_id: int = 10) -> None:
        self.tx_repo.seed(
            owner_id=self.owner_id,
            account_id=account_id,
            kind=kind,
            amount=Decimal(amount),
            date=tx_date,
            description="x",
        )

    def test_monthly_summary_with_buckets_and_current_period(self) -> None:
        # Income 2 months back (complete bucket), expense in current period (today).
        self._seed(self._months_ago_date(2), "income", "1000.00")
        self._seed(self.today, "expense", "300.00")

        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=2
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.period, "month")
        self.assertEqual(out.periods_count, 2)
        self.assertEqual(len(out.buckets), 2)
        self.assertIsNotNone(out.current_period)
        self.assertTrue(out.current_period.is_partial)

        # The expense today falls in the current (partial) period.
        self.assertEqual(out.current_period.expense, "300.00")
        self.assertEqual(out.current_period.income, "0.00")
        # The income 2 months back falls in one of the complete buckets.
        total_income_complete = sum(Decimal(b.income) for b in out.buckets)
        total_expense_complete = sum(Decimal(b.expense) for b in out.buckets)
        self.assertEqual(total_income_complete, Decimal("1000.00"))
        self.assertEqual(total_expense_complete, Decimal("0.00"))

    def test_current_period_is_partial_with_days_metadata(self) -> None:
        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=1
            )
        )
        self.assertTrue(result.is_success)
        cp = result.value.current_period
        self.assertTrue(cp.is_partial)
        self.assertGreaterEqual(cp.days_elapsed, 1)
        self.assertGreaterEqual(cp.days_total, cp.days_elapsed)
        # For month, days_total is month length (28-31).
        self.assertGreaterEqual(cp.days_total, 28)
        self.assertLessEqual(cp.days_total, 31)

    def test_current_period_txs_not_in_complete_buckets(self) -> None:
        self._seed(self.today, "income", "500.00")
        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=3
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        # All complete buckets empty, current has the income.
        for b in out.buckets:
            self.assertEqual(b.income, "0.00")
            self.assertEqual(b.expense, "0.00")
        self.assertEqual(out.current_period.income, "500.00")

    def test_excludes_transfer_transactions(self) -> None:
        # Expense 2 months back (counts now, transfer filtering removed).
        self.tx_repo.seed(
            owner_id=self.owner_id,
            account_id=self.account_a,
            kind="expense",
            amount=Decimal("2000.00"),
            date=self._months_ago_date(2),
        )
        # Normal income 2 months back (counted).
        self._seed(self._months_ago_date(2), "income", "1000.00")

        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=3
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        all_expense = sum(Decimal(b.expense) for b in out.buckets) + Decimal(
            out.current_period.expense
        )
        all_income = sum(Decimal(b.income) for b in out.buckets) + Decimal(
            out.current_period.income
        )
        self.assertEqual(all_expense, Decimal("2000.00"))
        self.assertEqual(all_income, Decimal("1000.00"))

    def test_account_filter_only_sums_that_account(self) -> None:
        self._seed(self._months_ago_date(2), "income", "1000.00", account_id=self.account_a)
        self._seed(self._months_ago_date(2), "income", "500.00", account_id=self.account_b)

        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id,
                period="month",
                periods_count=3,
                account_id=self.account_a,
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        total_income = sum(Decimal(b.income) for b in out.buckets) + Decimal(
            out.current_period.income
        )
        self.assertEqual(total_income, Decimal("1000.00"))

    def test_no_transactions_all_buckets_zero(self) -> None:
        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=2
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(len(out.buckets), 2)
        for b in out.buckets:
            self.assertEqual(b.income, "0.00")
            self.assertEqual(b.expense, "0.00")
            self.assertEqual(b.net, "0.00")
        self.assertEqual(out.current_period.income, "0.00")
        self.assertEqual(out.current_period.expense, "0.00")
        self.assertEqual(out.current_period.net, "0.00")

    def test_weekly_summary_keys_and_labels(self) -> None:
        # Seed an income 3 weeks back (in a complete bucket).
        target = self._week_start(self.today) - timedelta(weeks=3) + timedelta(days=2)
        self._seed(target, "income", "100.00")
        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="week", periods_count=3
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(len(out.buckets), 3)
        for b in out.buckets:
            self.assertRegex(b.label, r"^\d{2}/\d{2}$")
            self.assertRegex(b.key, r"^\d{4}-W\d{2}$")
        total_income = sum(Decimal(b.income) for b in out.buckets) + Decimal(
            out.current_period.income
        )
        self.assertEqual(total_income, Decimal("100.00"))

    def test_yearly_summary_keys_and_labels(self) -> None:
        # Income last year (complete bucket).
        self._seed(self._years_ago_date(1), "income", "5000.00")
        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="year", periods_count=2
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(len(out.buckets), 2)
        for b in out.buckets:
            self.assertRegex(b.key, r"^\d{4}$")
            self.assertRegex(b.label, r"^\d{4}$")
        total_income = sum(Decimal(b.income) for b in out.buckets)
        self.assertEqual(total_income, Decimal("5000.00"))

    def test_periods_count_one_single_complete_bucket_plus_current(self) -> None:
        self._seed(self._months_ago_date(1), "income", "100.00")
        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=1
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(len(out.buckets), 1)
        self.assertIsNotNone(out.current_period)

    def test_invalid_period(self) -> None:
        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="decade", periods_count=2
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "period")
        self.assertEqual(result.errors[0].code, "reports.period.invalid")

    def test_periods_count_out_of_range_zero(self) -> None:
        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=0
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "periods_count")
        self.assertEqual(result.errors[0].code, "reports.periods_count.invalid")

    def test_periods_count_out_of_range_thirteen(self) -> None:
        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=13
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "periods_count")
        self.assertEqual(result.errors[0].code, "reports.periods_count.invalid")

    def test_net_is_income_minus_expense_per_bucket(self) -> None:
        # Income and expense 2 months back (same complete bucket).
        self._seed(self._months_ago_date(2), "income", "700.00")
        self._seed(self._months_ago_date(2), "expense", "250.00")
        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=3
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        for b in out.buckets:
            expected_net = Decimal(b.income) - Decimal(b.expense)
            self.assertEqual(Decimal(b.net), expected_net)
        expected_cp_net = Decimal(out.current_period.income) - Decimal(
            out.current_period.expense
        )
        self.assertEqual(Decimal(out.current_period.net), expected_cp_net)

    def test_buckets_ordered_old_to_new(self) -> None:
        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="year", periods_count=3
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        keys = [int(b.key) for b in out.buckets]
        self.assertEqual(keys, sorted(keys))
        # current_period key is strictly greater than last complete bucket key.
        cp_key = int(out.current_period.key)
        self.assertGreater(cp_key, keys[-1])

    def test_only_owner_transactions_counted(self) -> None:
        self.tx_repo.seed(
            owner_id=999,
            account_id=self.account_a,
            kind="income",
            amount=Decimal("9999.00"),
            date=self._months_ago_date(2),
        )
        self._seed(self._months_ago_date(2), "income", "100.00")
        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=3
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        total = sum(Decimal(b.income) for b in out.buckets) + Decimal(
            out.current_period.income
        )
        self.assertEqual(total, Decimal("100.00"))


class TestIncomeExpenseAccumulated(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.tx_repo = InMemoryTransactionRepository()
        self.account_repo = InMemoryAccountRepository()
        self.use_case = GetIncomeExpenseSummaryUseCase(
            repository=self.tx_repo,
            account_repository=self.account_repo,
        )
        self.today = date.today()
        self.owner_id = 1

    def tearDown(self) -> None:
        translation.deactivate_all()

    def _months_ago_date(self, months_back: int, day: int = 15) -> date:
        idx = self.today.year * 12 + (self.today.month - 1) - months_back
        year, month = divmod(idx, 12)
        return date(year, month + 1, day)

    def _seed(self, tx_date: date, kind: str, amount: str, account_id: int) -> None:
        self.tx_repo.seed(
            owner_id=self.owner_id,
            account_id=account_id,
            kind=kind,
            amount=Decimal(amount),
            date=tx_date,
            description="x",
        )

    def test_accumulated_running_balance_with_initial_balance(self) -> None:
        account = self.account_repo.seed(
            owner_id=1, name="Banco", initial_balance=Decimal("500.00")
        )
        # Before the window (3 months back, window starts 2 months back): +1000 income
        self._seed(self._months_ago_date(3), "income", "1000.00", account.id)
        # Current period: -300 expense
        self._seed(self.today, "expense", "300.00", account.id)

        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=1, period="month", periods_count=2,
                account_id=account.id,
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        # accumulated has len(buckets) + 1 (current)
        self.assertEqual(len(out.accumulated), len(out.buckets) + 1)
        # initial = 500 (account) + 1000 (prior tx) = 1500
        # first bucket (2 months ago): 1500 + 0 = 1500
        self.assertEqual(out.accumulated[0], "1500.00")
        # second bucket (1 month ago): 1500 + 0 = 1500
        self.assertEqual(out.accumulated[1], "1500.00")
        # current: 1500 - 300 = 1200
        self.assertEqual(out.accumulated[-1], "1200.00")

    def test_accumulated_without_account_id_no_accounts_seeded(self) -> None:
        # No accounts seeded -> initial_balance sum is 0; tx lands in first bucket.
        self._seed(self._months_ago_date(2), "income", "1000.00", 10)
        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=1, period="month", periods_count=2,
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(len(out.accumulated), len(out.buckets) + 1)
        # initial 0; first bucket +1000; rest carry forward
        self.assertEqual(out.accumulated[0], "1000.00")
        self.assertEqual(out.accumulated[-1], "1000.00")

    def test_accumulated_includes_transfers_by_account(self) -> None:
        source = self.account_repo.seed(
            owner_id=1, name="Efectivo", initial_balance=Decimal("1000.00")
        )
        dest = self.account_repo.seed(
            owner_id=1, name="Banco", initial_balance=Decimal("0.00")
        )
        # Expense from source and income to dest before the window
        self.tx_repo.seed(
            owner_id=1, account_id=source.id, kind="expense",
            amount=Decimal("400"), date=self._months_ago_date(3),
            description="transfer out",
        )
        self.tx_repo.seed(
            owner_id=1, account_id=dest.id, kind="income",
            amount=Decimal("400"), date=self._months_ago_date(3),
            description="transfer in",
        )

        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=1, period="month", periods_count=2,
                account_id=dest.id,
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        # dest initial_balance = 0, prior income = +400 -> initial 400
        # no movements in window -> all 400
        for amt in out.accumulated:
            self.assertEqual(amt, "400.00")

    def test_accumulated_sums_all_active_accounts_without_account_id(self) -> None:
        # Two active accounts: 500 + 300 = 800
        a1 = self.account_repo.seed(
            owner_id=1, name="Efectivo", initial_balance=Decimal("500.00")
        )
        a2 = self.account_repo.seed(
            owner_id=1, name="Banco", initial_balance=Decimal("300.00")
        )
        # Previous period (3 months back, before window): +400 on a1
        self._seed(self._months_ago_date(3), "income", "400.00", a1.id)

        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=1, period="month", periods_count=2,
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        # initial = 800 (sum active) + 400 (prior tx) = 1200; no window movements
        for amt in out.accumulated:
            self.assertEqual(amt, "1200.00")

    def test_accumulated_excludes_inactive_accounts_without_account_id(self) -> None:
        active = self.account_repo.seed(
            owner_id=1, name="Efectivo", initial_balance=Decimal("500.00")
        )
        inactive = self.account_repo.seed(
            owner_id=1, name="Vieja", initial_balance=Decimal("9999.00")
        )
        self.account_repo.deactivate(inactive.id)
        # Previous period tx: +400
        self._seed(self._months_ago_date(3), "income", "400.00", active.id)

        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=1, period="month", periods_count=2,
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        # initial = 500 (only active) + 400 = 900 (inactive 9999 excluded)
        for amt in out.accumulated:
            self.assertEqual(amt, "900.00")


class TestGetIncomeExpenseSummaryFixedVariableSplit(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.tx_repo = InMemoryTransactionRepository()
        self.category_repo = InMemoryCategoryRepository()
        self.use_case = GetIncomeExpenseSummaryUseCase(
            repository=self.tx_repo,
            category_repository=self.category_repo,
        )
        self.today = date.today()
        self.owner_id = 1

    def tearDown(self) -> None:
        translation.deactivate_all()

    def _months_ago_date(self, months_back: int, day: int = 15) -> date:
        idx = self.today.year * 12 + (self.today.month - 1) - months_back
        year, month = divmod(idx, 12)
        return date(year, month + 1, day)

    def _seed(
        self,
        tx_date: date,
        kind: str,
        amount: str,
        account_id: int = 10,
        category_id: Optional[int] = None,
    ) -> None:
        self.tx_repo.seed(
            owner_id=self.owner_id,
            account_id=account_id,
            kind=kind,
            amount=Decimal(amount),
            date=tx_date,
            description="x",
            category_id=category_id,
        )

    def test_expense_with_fixed_category_lands_in_expense_fixed(self) -> None:
        cat_fixed = self.category_repo.seed(
            owner_id=self.owner_id, name="Alquiler", kind="expense", is_fixed=True
        )
        self._seed(self.today, "expense", "500.00", category_id=cat_fixed.id)

        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=2
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.current_period.expense_fixed, "500.00")
        self.assertEqual(out.current_period.expense_variable, "0.00")
        self.assertEqual(out.current_period.expense, "500.00")

    def test_expense_with_variable_category_lands_in_expense_variable(self) -> None:
        cat_var = self.category_repo.seed(
            owner_id=self.owner_id, name="Salidas a comer", kind="expense", is_fixed=False
        )
        self._seed(self.today, "expense", "120.00", category_id=cat_var.id)

        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=2
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.current_period.expense_fixed, "0.00")
        self.assertEqual(out.current_period.expense_variable, "120.00")
        self.assertEqual(out.current_period.expense, "120.00")

    def test_uncategorized_expense_lands_in_expense_variable(self) -> None:
        self._seed(self.today, "expense", "75.00", category_id=None)

        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=2
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.current_period.expense_fixed, "0.00")
        self.assertEqual(out.current_period.expense_variable, "75.00")
        self.assertEqual(out.current_period.expense, "75.00")

    def test_patrimonial_expense_excluded_from_fixed_and_variable(self) -> None:
        cat_pat = self.category_repo.seed(
            owner_id=self.owner_id,
            name="Aporte de capital",
            kind="expense",
            include_in_summaries=False,
            is_fixed=True,
        )
        self._seed(self.today, "expense", "1000.00", category_id=cat_pat.id)

        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=2
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.current_period.expense, "0.00")
        self.assertEqual(out.current_period.expense_fixed, "0.00")
        self.assertEqual(out.current_period.expense_variable, "0.00")
        self.assertEqual(out.current_period.balance_movement_outflow, "1000.00")

    def test_split_invariant_fixed_plus_variable_equals_expense(self) -> None:
        cat_fixed = self.category_repo.seed(
            owner_id=self.owner_id, name="Alquiler", kind="expense", is_fixed=True
        )
        cat_var = self.category_repo.seed(
            owner_id=self.owner_id, name="Salidas", kind="expense", is_fixed=False
        )
        target_date = self._months_ago_date(2)
        self._seed(target_date, "expense", "300.00", category_id=cat_fixed.id)
        self._seed(target_date, "expense", "200.00", category_id=cat_var.id)
        self._seed(self.today, "expense", "100.00", category_id=None)

        result = self.use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=self.owner_id, period="month", periods_count=3
            )
        )
        self.assertTrue(result.is_success)
        out = result.value

        for b in out.buckets:
            self.assertEqual(
                Decimal(b.expense_fixed) + Decimal(b.expense_variable),
                Decimal(b.expense),
                msg=f"Bucket {b.key} violates fixed+variable==expense",
            )
        self.assertEqual(
            Decimal(out.current_period.expense_fixed)
            + Decimal(out.current_period.expense_variable),
            Decimal(out.current_period.expense),
        )

        target_bucket = next(b for b in out.buckets if Decimal(b.expense) > 0)
        self.assertEqual(target_bucket.expense_fixed, "300.00")
        self.assertEqual(target_bucket.expense_variable, "200.00")
        self.assertEqual(target_bucket.expense, "500.00")
        self.assertEqual(out.current_period.expense_fixed, "0.00")
        self.assertEqual(out.current_period.expense_variable, "100.00")
        self.assertEqual(out.current_period.expense, "100.00")


if __name__ == "__main__":
    unittest.main()