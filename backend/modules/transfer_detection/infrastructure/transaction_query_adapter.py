from __future__ import annotations

from datetime import date
from typing import Optional

from modules.transactions.domain.entities import Transaction
from modules.transactions.infrastructure.repositories import (
    DjangoTransactionRepository,
)
from modules.transfer_detection.application.ports import TransactionQueryPort


class DjangoTransactionQueryAdapter(TransactionQueryPort):
    """Adapta ``DjangoTransactionRepository`` al port ``TransactionQueryPort``."""

    def __init__(self, repository: Optional[DjangoTransactionRepository] = None) -> None:
        self._repository = repository or DjangoTransactionRepository()

    def list_unlinked_by_owner(
        self,
        owner_id: int,
        account_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> list[Transaction]:
        return self._repository.list_by_owner(
            owner_id=owner_id,
            account_id=account_id,
            transfer_group_id_isnull=True,
            date_from=date_from,
            date_to=date_to,
        )