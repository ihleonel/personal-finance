from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CreateCategorizationRuleInput:
    owner_id: int
    pattern: str
    match_type: str
    category_id: int
    kind: str
    priority: int = 0


@dataclass(frozen=True)
class UpdateCategorizationRuleInput:
    pattern: Optional[str] = None
    match_type: Optional[str] = None
    category_id: Optional[int] = None
    kind: Optional[str] = None
    priority: Optional[int] = None


@dataclass(frozen=True)
class CategorizationRuleOutput:
    id: int
    owner_id: int
    pattern: str
    match_type: str
    category_id: int
    kind: str
    priority: int
    is_active: bool


@dataclass(frozen=True)
class SuggestCategoryInput:
    owner_id: int
    description: str


@dataclass(frozen=True)
class SuggestCategoryOutput:
    category_id: Optional[int]
    category_name: Optional[str]