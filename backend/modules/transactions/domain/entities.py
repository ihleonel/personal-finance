from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class Transaction:
    id: Optional[int]
    owner_id: int
    account_id: int
    category_id: Optional[int]
    kind: str
    amount: Decimal
    date: date
    description: str = ""
    transfer_group_id: Optional[UUID] = None
    source: str = ""
    external_reference: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)