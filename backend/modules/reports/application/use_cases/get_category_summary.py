from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from django.utils.translation import gettext_lazy as _

from modules.accounts.domain.repositories import AccountRepository
from modules.categories.domain.repositories import CategoryRepository
from modules.reports.application import period_utils
from modules.reports.application.dtos import (
    CategoryPeriodColumnOutput,
    CategoryRowOutput,
    CategorySummaryInput,
    CategorySummaryOutput,
    CategoryTotalsOutput,
)
from modules.shared.application.result import Result
from modules.transactions.domain.repositories import TransactionRepository


@dataclass
class GetCategorySummaryUseCase:
    repository: TransactionRepository
    category_repository: Optional[CategoryRepository] = None
    account_repository: Optional[AccountRepository] = None

    def execute(self, data: CategorySummaryInput) -> Result[CategorySummaryOutput]:
        result = Result[CategorySummaryOutput]()

        if data.period not in period_utils.VALID_PERIODS:
            result.add_error(
                "period",
                "reports.period.invalid",
                str(_("El periodo debe ser 'week', 'month' o 'year'.")),
            )

        if data.periods_count < 1 or data.periods_count > 12:
            result.add_error(
                "periods_count",
                "reports.periods_count.invalid",
                str(_("La cantidad de periodos debe ser un entero entre 1 y 12.")),
            )

        if result.has_errors:
            return result

        today = date.today()
        current_start = period_utils.period_start(data.period, today)
        complete_from = period_utils.shift_periods(data.period, current_start, data.periods_count)

        txs = self.repository.list_by_owner(
            owner_id=data.owner_id,
            account_id=data.account_id,
            transfer_group_id_isnull=True,
            date_from=complete_from,
            date_to=today,
        )

        categories = (
            self.category_repository.list_by_owner(data.owner_id)
            if self.category_repository is not None
            else []
        )

        # All categories grouped by kind, ordered by name. Includes inactive ones.
        cats_by_id: dict[int, object] = {c.id: c for c in categories}
        income_cats = sorted(
            [c for c in categories if c.kind == "income"],
            key=lambda c: _sort_key(c.name),
        )
        expense_cats = sorted(
            [c for c in categories if c.kind == "expense"],
            key=lambda c: _sort_key(c.name),
        )

        # Column keys: N complete buckets + 1 current (partial) at the end.
        column_keys: list[str] = []
        for i in range(data.periods_count):
            start = period_utils.add_periods(data.period, complete_from, i)
            key, _label = period_utils.bucket_key_and_label(data.period, start)
            column_keys.append(key)
        current_key, current_label = period_utils.bucket_key_and_label(
            data.period, current_start
        )
        column_keys.append(current_key)
        key_to_index: dict[str, int] = {k: i for i, k in enumerate(column_keys)}

        # amounts_by_cat: (category_id_or_None, kind) -> list[Decimal] per column
        n_cols = len(column_keys)
        amounts: dict[tuple[Optional[int], str], list[Decimal]] = {}

        def _slot(key: tuple[Optional[int], str]) -> list[Decimal]:
            if key not in amounts:
                amounts[key] = [period_utils.ZERO] * n_cols
            return amounts[key]

        for tx in txs:
            bucket_key = period_utils.tx_bucket_key(data.period, tx.date)
            idx = key_to_index.get(bucket_key)
            if idx is None:
                continue
            slot_key = (tx.category_id, tx.kind)
            _slot(slot_key)[idx] += tx.amount

        # Detect which uncategorized (category_id=None) kinds have movement
        uncategorized_kinds: set[str] = {
            kind for (cat_id, kind) in amounts if cat_id is None
        }

        # Build columns output
        columns: list[CategoryPeriodColumnOutput] = []
        for i, key in enumerate(column_keys):
            is_partial = i == n_cols - 1
            if is_partial:
                label = current_label
                days_elapsed, days_total = period_utils.days_elapsed_and_total(
                    data.period, current_start, today
                )
                columns.append(
                    CategoryPeriodColumnOutput(
                        key=key,
                        label=label,
                        is_partial=True,
                        days_elapsed=days_elapsed,
                        days_total=days_total,
                    )
                )
            else:
                label = period_utils.label_for_key(data.period, key)
                columns.append(CategoryPeriodColumnOutput(key=key, label=label))

        rows: list[CategoryRowOutput] = []

        def _row_for_category(cat, kind: str) -> CategoryRowOutput:
            slot = amounts.get((cat.id, kind), [period_utils.ZERO] * n_cols)
            return CategoryRowOutput(
                category_id=cat.id,
                name=cat.name,
                kind=kind,
                is_uncategorized=False,
                is_active=cat.is_active,
                amounts=[period_utils.fmt(v) for v in slot],
            )

        def _row_uncategorized(kind: str) -> CategoryRowOutput:
            slot = amounts.get((None, kind), [period_utils.ZERO] * n_cols)
            return CategoryRowOutput(
                category_id=None,
                name="Sin categoría",
                kind=kind,
                is_uncategorized=True,
                is_active=True,
                amounts=[period_utils.fmt(v) for v in slot],
            )

        # Income rows: active+inactive income categories (already sorted) then "Sin categoría"
        for cat in income_cats:
            rows.append(_row_for_category(cat, "income"))
        if "income" in uncategorized_kinds:
            rows.append(_row_uncategorized("income"))

        # Expense rows: same pattern
        for cat in expense_cats:
            rows.append(_row_for_category(cat, "expense"))
        if "expense" in uncategorized_kinds:
            rows.append(_row_uncategorized("expense"))

        # Totals: net per column = income - expense across all rows
        totals_amounts = [period_utils.ZERO] * n_cols
        for row in rows:
            sign = Decimal("1") if row.kind == "income" else Decimal("-1")
            for i, amt in enumerate(row.amounts):
                totals_amounts[i] += sign * Decimal(amt)

        # Accumulated balance per column: initial balance + running sum of nets.
        # Initial balance = net of all transactions strictly before the window.
        previous_txs = self.repository.list_by_owner(
            owner_id=data.owner_id,
            account_id=data.account_id,
            transfer_group_id_isnull=True,
            date_to=complete_from - timedelta(days=1),
        )
        initial_balance = period_utils.ZERO
        if self.account_repository is not None:
            initial_balance = period_utils.sum_active_initial_balances(
                self.account_repository, data.owner_id, data.account_id
            )
        for tx in previous_txs:
            initial_balance += tx.amount if tx.kind == "income" else -tx.amount
        accumulated_amounts: list[Decimal] = []
        running = initial_balance
        for net in totals_amounts:
            running += net
            accumulated_amounts.append(running)

        totals = CategoryTotalsOutput(
            amounts=[period_utils.fmt(v) for v in totals_amounts],
            accumulated=[period_utils.fmt(v) for v in accumulated_amounts],
        )

        return Result.ok(
            CategorySummaryOutput(
                period=data.period,
                periods_count=data.periods_count,
                columns=columns,
                rows=rows,
                totals=totals,
            )
        )


def _sort_key(name: str) -> str:
    return (name or "").lower()