from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CreateCategoryInput:
    owner_id: int
    name: str
    kind: str


@dataclass(frozen=True)
class UpdateCategoryInput:
    name: Optional[str] = None
    kind: Optional[str] = None


@dataclass(frozen=True)
class CategoryOutput:
    id: int
    owner_id: int
    name: str
    kind: str
    is_active: bool