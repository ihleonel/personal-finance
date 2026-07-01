from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .entities import CategorizationRule


class CategorizationRuleRepository(ABC):
    """Domain port for categorization rule persistence."""

    @abstractmethod
    def save(
        self,
        owner_id: int,
        pattern: str,
        match_type: str,
        category_id: int,
        kind: str,
        priority: int,
    ) -> CategorizationRule: ...

    @abstractmethod
    def find_by_id(self, rule_id: int) -> Optional[CategorizationRule]: ...

    @abstractmethod
    def list_by_owner(self, owner_id: int) -> list[CategorizationRule]: ...

    @abstractmethod
    def list_active_by_owner(self, owner_id: int) -> list[CategorizationRule]: ...

    @abstractmethod
    def update(
        self,
        rule_id: int,
        pattern: Optional[str] = None,
        match_type: Optional[str] = None,
        category_id: Optional[int] = None,
        kind: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> CategorizationRule: ...

    @abstractmethod
    def deactivate(self, rule_id: int) -> CategorizationRule: ...

    @abstractmethod
    def activate(self, rule_id: int) -> CategorizationRule: ...

    @abstractmethod
    def delete(self, rule_id: int) -> None: ...

    @abstractmethod
    def exists_active_duplicate_for_owner(
        self,
        owner_id: int,
        pattern: str,
        match_type: str,
        exclude_id: Optional[int] = None,
    ) -> bool: ...