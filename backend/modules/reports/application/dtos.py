from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class IncomeExpenseSummaryInput:
    owner_id: int
    period: str
    periods_count: int
    account_id: Optional[int] = None


@dataclass(frozen=True)
class PeriodBucketOutput:
    key: str
    label: str
    income: str
    expense: str
    net: str
    balance_movement_inflow: str = "0.00"
    balance_movement_outflow: str = "0.00"
    balance_movement_net: str = "0.00"


@dataclass(frozen=True)
class CurrentPeriodOutput:
    key: str
    label: str
    income: str
    expense: str
    net: str
    is_partial: bool
    days_elapsed: int
    days_total: int
    balance_movement_inflow: str = "0.00"
    balance_movement_outflow: str = "0.00"
    balance_movement_net: str = "0.00"


@dataclass(frozen=True)
class IncomeExpenseSummaryOutput:
    period: str
    periods_count: int
    buckets: list[PeriodBucketOutput]
    current_period: CurrentPeriodOutput
    accumulated: list[str]


@dataclass(frozen=True)
class CategorySummaryInput:
    owner_id: int
    period: str
    periods_count: int
    account_id: Optional[int] = None
    only_patrimonial: bool = False


@dataclass(frozen=True)
class CategoryPeriodColumnOutput:
    key: str
    label: str
    is_partial: bool = False
    days_elapsed: int = 0
    days_total: int = 0


@dataclass(frozen=True)
class CategoryRowOutput:
    category_id: Optional[int]
    name: str
    kind: str
    is_uncategorized: bool
    is_active: bool
    amounts: list[str]
    include_in_summaries: bool = True


@dataclass(frozen=True)
class CategoryTotalsOutput:
    amounts: list[str]
    accumulated: list[str]


@dataclass(frozen=True)
class CategorySummaryOutput:
    period: str
    periods_count: int
    columns: list[CategoryPeriodColumnOutput]
    rows: list[CategoryRowOutput]
    totals: CategoryTotalsOutput