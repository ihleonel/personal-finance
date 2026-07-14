"""Shared period helpers for reports use cases.

Extracted from GetIncomeExpenseSummaryUseCase so both income-expense and
category-summary use cases reuse the same period arithmetic and formatting.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP


VALID_PERIODS = ("week", "month", "year")
MES_ES = (
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
)
Q = Decimal("0.01")
ZERO = Decimal("0.00")


def fmt(value: Decimal) -> str:
    return str(value.quantize(Q, rounding=ROUND_HALF_UP))


def period_start(period: str, d: date) -> date:
    if period == "week":
        return d - timedelta(days=d.weekday())
    if period == "month":
        return d.replace(day=1)
    return d.replace(month=1, day=1)


def shift_periods(period: str, start: date, n: int) -> date:
    if period == "week":
        return start - timedelta(weeks=n)
    if period == "month":
        idx = start.year * 12 + (start.month - 1) - n
        year, month = divmod(idx, 12)
        return date(year, month + 1, 1)
    return date(start.year - n, 1, 1)


def add_periods(period: str, start: date, n: int) -> date:
    if period == "week":
        return start + timedelta(weeks=n)
    if period == "month":
        idx = start.year * 12 + (start.month - 1) + n
        year, month = divmod(idx, 12)
        return date(year, month + 1, 1)
    return date(start.year + n, 1, 1)


def bucket_key_and_label(period: str, start: date) -> tuple[str, str]:
    if period == "week":
        iso_year, iso_week, _ = start.isocalendar()
        return f"{iso_year}-W{iso_week:02d}", start.strftime("%d/%m")
    if period == "month":
        return f"{start.year}-{start.month:02d}", f"{MES_ES[start.month - 1]} {start.year}"
    return f"{start.year}", f"{start.year}"


def tx_bucket_key(period: str, tx_date: date) -> str:
    if period == "week":
        iso_year, iso_week, _ = tx_date.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    if period == "month":
        return f"{tx_date.year}-{tx_date.month:02d}"
    return f"{tx_date.year}"


def label_for_key(period: str, key: str) -> str:
    if period == "week":
        year_part, week_part = key.split("-W")
        year = int(year_part)
        week = int(week_part)
        monday = monday_of_iso_week(year, week)
        return monday.strftime("%d/%m")
    if period == "month":
        year_part, month_part = key.split("-")
        return f"{MES_ES[int(month_part) - 1]} {int(year_part)}"
    return key


def monday_of_iso_week(year: int, week: int) -> date:
    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=jan4.weekday())
    return week1_monday + timedelta(weeks=week - 1)


def days_elapsed_and_total(period: str, start: date, today: date) -> tuple[int, int]:
    if period == "week":
        return (today - start).days + 1, 7
    if period == "month":
        days_total = calendar.monthrange(start.year, start.month)[1]
        return today.day, days_total
    is_leap = calendar.isleap(start.year)
    days_total = 366 if is_leap else 365
    days_elapsed = (today - start).days + 1
    return days_elapsed, days_total


def sum_active_initial_balances(
    account_repository,
    owner_id: int,
    account_id: int | None,
) -> Decimal:
    """Sum the initial_balance of the relevant active accounts.

    If account_id is provided, returns that account's initial_balance when it
    exists and belongs to owner_id; otherwise ZERO. When account_id is None,
    sums initial_balance across all active accounts of the owner (ignoring
    currency, consistent with the aggregate report behaviour).
    """
    if account_id is not None:
        account = account_repository.find_by_id(account_id)
        if account is not None and account.owner_id == owner_id:
            return account.initial_balance
        return ZERO
    total = ZERO
    for account in account_repository.list_by_owner(owner_id):
        if account.is_active:
            total += account.initial_balance
    return total