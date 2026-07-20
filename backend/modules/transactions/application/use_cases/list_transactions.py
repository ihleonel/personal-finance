from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from modules.shared.application.result import Result
from modules.transactions.application.dtos import (
    ListTransactionsFilters,
    TransactionOutput,
)
from modules.transactions.domain.repositories import TransactionRepository


@dataclass
class ListTransactionsUseCase:
    repository: TransactionRepository

    def execute(
        self,
        owner_id: int,
        filters: Optional[ListTransactionsFilters] = None,
    ) -> Result[list[TransactionOutput]]:
        filters = filters or ListTransactionsFilters()

        date_from = self._parse_date(filters.date_from)
        date_to = self._parse_date(filters.date_to)

        txs = self.repository.list_by_owner(
            owner_id=owner_id,
            account_id=filters.account_id,
            kind=filters.kind,
            category_id=filters.category_id,
            category_id_isnull=filters.category_id_isnull,
            date_from=date_from,
            date_to=date_to,
            description=filters.description,
        )
        outputs = [self._to_output(t) for t in txs]
        return Result.ok(outputs)

    @staticmethod
    def _parse_date(raw: Optional[str]) -> Optional[date]:
        if raw is None or raw == "":
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return None

    @staticmethod
    def _to_output(tx) -> TransactionOutput:
        return TransactionOutput(
            id=tx.id or 0,
            owner_id=tx.owner_id,
            account_id=tx.account_id,
            category_id=tx.category_id,
            kind=tx.kind,
            amount=str(tx.amount),
            date=tx.date.isoformat() if hasattr(tx.date, "isoformat") else str(tx.date),
            description=tx.description,
            created_at=tx.created_at.isoformat() if hasattr(tx.created_at, "isoformat") else str(tx.created_at),
        )