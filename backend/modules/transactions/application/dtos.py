from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from modules.shared.domain.optional import UNSET


@dataclass(frozen=True)
class CreateTransactionInput:
    owner_id: int
    account_id: int
    kind: str
    amount: str
    date: str
    category_id: Optional[int] = None
    description: str = ""


@dataclass(frozen=True)
class CreateTransferInput:
    owner_id: int
    source_account_id: int
    destination_account_id: int
    amount: str
    date: str
    description: str = ""
    category_id: Optional[int] = None


@dataclass(frozen=True)
class UpdateTransactionInput:
    amount: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None
    category_id: Any = field(default=UNSET)

    @property
    def is_category_id_set(self) -> bool:
        return self.category_id is not UNSET


@dataclass(frozen=True)
class ListTransactionsFilters:
    account_id: Optional[int] = None
    kind: Optional[str] = None
    category_id: Optional[int] = None
    category_id_isnull: bool = False
    date_from: Optional[str] = None
    date_to: Optional[str] = None


@dataclass(frozen=True)
class TransactionOutput:
    id: int
    owner_id: int
    account_id: int
    category_id: Optional[int]
    kind: str
    amount: str
    date: str
    description: str
    transfer_group_id: Optional[str]
    created_at: str
    suggested_category_id: Optional[int] = None


@dataclass(frozen=True)
class TransferOutput:
    source: TransactionOutput
    destination: TransactionOutput


@dataclass(frozen=True)
class ImportTransactionRowInput:
    account_id: int
    date: str
    amount: str
    description: str
    external_reference: str


@dataclass(frozen=True)
class ImportSkippedRow:
    row_number: int
    external_reference: str
    reason: str


@dataclass(frozen=True)
class ImportErrorRow:
    row_number: int
    field: str
    message: str


@dataclass(frozen=True)
class ImportSummary:
    total: int
    created: int
    skipped: int
    errors: int


@dataclass(frozen=True)
class ImportTransactionResult:
    created: list[TransactionOutput]
    skipped: list[ImportSkippedRow]
    errors: list[ImportErrorRow]
    summary: ImportSummary