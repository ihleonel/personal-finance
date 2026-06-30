from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from .entities import Account


class AccountRepository(ABC):
    """Domain port for account persistence. Implemented by infrastructure."""

    @abstractmethod
    def save(
        self,
        owner_id: int,
        name: str,
        account_type: str,
        currency: str,
        initial_balance: Decimal,
    ) -> Account: ...

    @abstractmethod
    def find_by_id(self, account_id: int) -> Optional[Account]: ...

    @abstractmethod
    def list_by_owner(self, owner_id: int) -> list[Account]: ...

    @abstractmethod
    def update(
        self,
        account_id: int,
        name: Optional[str] = None,
        account_type: Optional[str] = None,
        currency: Optional[str] = None,
        initial_balance: Optional[Decimal] = None,
    ) -> Account: ...

    @abstractmethod
    def deactivate(self, account_id: int) -> Account: ...

    @abstractmethod
    def activate(self, account_id: int) -> Account: ...

    @abstractmethod
    def exists_active_name_for_owner(self, owner_id: int, name: str) -> bool: ...