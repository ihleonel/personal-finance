from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from modules.shared.domain.optional import UNSET

from .entities import Transaction


class TransactionRepository(ABC):
    """Domain port for transaction persistence. Implemented by infrastructure."""

    @abstractmethod
    def save(
        self,
        owner_id: int,
        account_id: int,
        category_id: Optional[int],
        kind: str,
        amount: Decimal,
        date: date,
        description: str,
        source: str = "",
        external_reference: str = "",
    ) -> Transaction: ...

    @abstractmethod
    def find_existing(
        self,
        owner_id: int,
        account_id: int,
        source: str,
        external_reference: str,
        date: date,
        amount: Decimal,
        description: str,
    ) -> Optional[Transaction]: ...

    @abstractmethod
    def find_by_id(self, transaction_id: int) -> Optional[Transaction]: ...

    @abstractmethod
    def list_by_owner(
        self,
        owner_id: int,
        account_id: Optional[int] = None,
        kind: Optional[str] = None,
        category_id: Optional[int] = None,
        category_id_isnull: bool = False,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        description: Optional[str] = None,
    ) -> list[Transaction]: ...

    @abstractmethod
    def update(
        self,
        transaction_id: int,
        amount: Optional[Decimal] = None,
        date: Optional[date] = None,
        description: Optional[str] = None,
        category_id: object = UNSET,
    ) -> Transaction: ...

    @abstractmethod
    def delete(self, transaction_id: int) -> None: ...

    @abstractmethod
    def bulk_assign_category(
        self,
        owner_id: int,
        transaction_ids: list[int],
        category_id: Optional[int],
        expected_kind: Optional[str],
    ) -> "BulkAssignCategoryResult": ...


@dataclass
class BulkAssignCategoryResult:
    updated_count: int
    skipped_ids: list[int]
    skipped_kinds: list[int]