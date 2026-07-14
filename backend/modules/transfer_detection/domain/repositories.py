from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .entities import TransferDetectionRule


class TransferDetectionRuleRepository(ABC):
    """Domain port for transfer detection rule persistence."""

    @abstractmethod
    def save(
        self,
        owner_id: int,
        pattern: str,
        match_type: str,
        priority: int,
    ) -> TransferDetectionRule: ...

    @abstractmethod
    def find_by_id(self, rule_id: int) -> Optional[TransferDetectionRule]: ...

    @abstractmethod
    def list_by_owner(self, owner_id: int) -> list[TransferDetectionRule]: ...

    @abstractmethod
    def list_active_by_owner(self, owner_id: int) -> list[TransferDetectionRule]: ...

    @abstractmethod
    def update(
        self,
        rule_id: int,
        pattern: Optional[str] = None,
        match_type: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> TransferDetectionRule: ...

    @abstractmethod
    def deactivate(self, rule_id: int) -> TransferDetectionRule: ...

    @abstractmethod
    def activate(self, rule_id: int) -> TransferDetectionRule: ...

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