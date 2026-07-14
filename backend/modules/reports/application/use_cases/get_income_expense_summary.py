from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from django.utils.translation import gettext_lazy as _

from modules.accounts.domain.repositories import AccountRepository
from modules.reports.application.dtos import (
    CurrentPeriodOutput,
    IncomeExpenseSummaryInput,
    IncomeExpenseSummaryOutput,
    PeriodBucketOutput,
)
from modules.reports.application import period_utils
from modules.shared.application.result import Result
from modules.transactions.domain.repositories import TransactionRepository


_Q = period_utils.Q
_ZERO = period_utils.ZERO


@dataclass
class GetIncomeExpenseSummaryUseCase:
    repository: TransactionRepository
    account_repository: Optional[AccountRepository] = None

    def execute(self, data: IncomeExpenseSummaryInput) -> Result[IncomeExpenseSummaryOutput]:
        result = Result[IncomeExpenseSummaryOutput]()

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

        buckets_map: dict[str, dict[str, Decimal]] = {}
        buckets_order: list[str] = []
        for i in range(data.periods_count):
            start = period_utils.add_periods(data.period, complete_from, i)
            key, label = period_utils.bucket_key_and_label(data.period, start)
            buckets_map[key] = {"income": _ZERO, "expense": _ZERO}
            buckets_order.append(key)

        current_key, current_label = period_utils.bucket_key_and_label(data.period, current_start)
        current_acc: dict[str, Decimal] = {"income": _ZERO, "expense": _ZERO}

        for tx in txs:
            key = period_utils.tx_bucket_key(data.period, tx.date)
            if key == current_key:
                target = current_acc
            elif key in buckets_map:
                target = buckets_map[key]
            else:
                continue
            if tx.kind == "income":
                target["income"] += tx.amount
            elif tx.kind == "expense":
                target["expense"] += tx.amount

        buckets_out: list[PeriodBucketOutput] = []
        for key in buckets_order:
            acc = buckets_map[key]
            income = period_utils.fmt(acc["income"])
            expense = period_utils.fmt(acc["expense"])
            label = period_utils.label_for_key(data.period, key)
            buckets_out.append(
                PeriodBucketOutput(
                    key=key,
                    label=label,
                    income=income,
                    expense=expense,
                    net=period_utils.fmt(acc["income"] - acc["expense"]),
                )
            )

        days_elapsed, days_total = period_utils.days_elapsed_and_total(
            data.period, current_start, today
        )
        current_out = CurrentPeriodOutput(
            key=current_key,
            label=current_label,
            income=period_utils.fmt(current_acc["income"]),
            expense=period_utils.fmt(current_acc["expense"]),
            net=period_utils.fmt(current_acc["income"] - current_acc["expense"]),
            is_partial=True,
            days_elapsed=days_elapsed,
            days_total=days_total,
        )

        accumulated_amounts = self._compute_accumulated(
            data, complete_from, buckets_order, buckets_map, current_acc
        )

        return Result.ok(
            IncomeExpenseSummaryOutput(
                period=data.period,
                periods_count=data.periods_count,
                buckets=buckets_out,
                current_period=current_out,
                accumulated=[period_utils.fmt(v) for v in accumulated_amounts],
            )
        )

    def _compute_accumulated(
        self,
        data: IncomeExpenseSummaryInput,
        complete_from: date,
        buckets_order: list[str],
        buckets_map: dict[str, dict[str, Decimal]],
        current_acc: dict[str, Decimal],
    ) -> list[Decimal]:
        initial_balance = period_utils.ZERO
        if self.account_repository is not None:
            initial_balance = period_utils.sum_active_initial_balances(
                self.account_repository, data.owner_id, data.account_id
            )

        previous_txs = self.repository.list_by_owner(
            owner_id=data.owner_id,
            account_id=data.account_id,
            date_to=complete_from - timedelta(days=1),
        )
        for tx in previous_txs:
            initial_balance += tx.amount if tx.kind == "income" else -tx.amount

        running = initial_balance
        accumulated: list[Decimal] = []
        for key in buckets_order:
            acc = buckets_map[key]
            running += acc["income"] - acc["expense"]
            accumulated.append(running)
        running += current_acc["income"] - current_acc["expense"]
        accumulated.append(running)
        return accumulated