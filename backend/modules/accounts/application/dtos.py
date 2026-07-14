from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class CreateAccountInput:
    owner_id: int
    name: str
    account_type: str
    currency: str
    initial_balance: str = "0"


@dataclass(frozen=True)
class UpdateAccountInput:
    name: Optional[str] = None
    account_type: Optional[str] = None
    currency: Optional[str] = None
    initial_balance: Optional[str] = None


@dataclass(frozen=True)
class AccountOutput:
    id: int
    owner_id: int
    name: str
    account_type: str
    currency: str
    initial_balance: str
    is_active: bool


@dataclass(frozen=True)
class AccountBalanceOutput:
    account_id: int
    initial_balance: str
    current_balance: str
    as_of: Optional[str]