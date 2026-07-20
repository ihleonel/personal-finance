from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CreateCategoryInput:
    owner_id: int
    name: str
    kind: str
    include_in_summaries: bool = True


@dataclass(frozen=True)
class UpdateCategoryInput:
    name: Optional[str] = None
    kind: Optional[str] = None
    include_in_summaries: Optional[bool] = None


@dataclass(frozen=True)
class CategoryOutput:
    id: int
    owner_id: int
    name: str
    kind: str
    include_in_summaries: bool
    is_active: bool