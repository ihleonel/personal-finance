from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class User:
    id: Optional[int]
    email: str
    first_name: str
    last_name: str
    is_active: bool
    created_at: datetime = field(default_factory=datetime.utcnow)
