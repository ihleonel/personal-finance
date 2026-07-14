from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from modules.transactions.domain.entities import Transaction


class TransactionQueryPort(ABC):
    """Port para listar transacciones del owner sin ``transfer_group_id``."""

    @abstractmethod
    def list_unlinked_by_owner(
        self,
        owner_id: int,
        account_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> list[Transaction]: ...