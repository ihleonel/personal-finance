from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional
from uuid import UUID


_ALLOWED_KINDS = frozenset({"income", "expense"})


class InvalidTransactionKindError(ValueError):
    pass


class InvalidTransactionAmountError(ValueError):
    pass


class InvalidTransactionDateError(ValueError):
    pass


class InvalidTransferGroupIdError(ValueError):
    pass


@dataclass(frozen=True)
class TransactionKind:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or self.value not in _ALLOWED_KINDS:
            raise InvalidTransactionKindError(f"Invalid kind: {self.value!r}")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def try_parse(cls, raw: object) -> Optional["TransactionKind"]:
        if not isinstance(raw, str):
            return None
        try:
            return cls(raw)
        except InvalidTransactionKindError:
            return None


@dataclass(frozen=True)
class TransactionAmount:
    value: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            raise InvalidTransactionAmountError(
                f"Invalid amount: {self.value!r}"
            )
        if self.value <= 0:
            raise InvalidTransactionAmountError(
                f"Amount must be positive: {self.value!r}"
            )

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def try_parse(cls, raw: object) -> Optional["TransactionAmount"]:
        if raw is None:
            return None
        try:
            value = Decimal(str(raw)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            return None
        try:
            return cls(value)
        except InvalidTransactionAmountError:
            return None


@dataclass(frozen=True)
class TransactionDate:
    value: date

    def __post_init__(self) -> None:
        if not isinstance(self.value, date):
            raise InvalidTransactionDateError(f"Invalid date: {self.value!r}")
        if self.value > date.today():
            raise InvalidTransactionDateError(
                f"Date cannot be in the future: {self.value!r}"
            )

    def __str__(self) -> str:
        return self.value.isoformat()

    @classmethod
    def try_parse(cls, raw: object) -> Optional["TransactionDate"]:
        if not isinstance(raw, (str, date)):
            return None
        if isinstance(raw, date) and not isinstance(raw, datetime):
            candidate = raw
        elif isinstance(raw, str):
            try:
                candidate = date.fromisoformat(raw)
            except ValueError:
                return None
        else:
            return None
        try:
            return cls(candidate)
        except InvalidTransactionDateError:
            return None


@dataclass(frozen=True)
class TransferGroupId:
    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise InvalidTransferGroupIdError(f"Invalid transfer group id: {self.value!r}")

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def try_parse(cls, raw: object) -> Optional["TransferGroupId"]:
        if raw is None:
            return None
        if isinstance(raw, UUID):
            return cls(raw)
        if isinstance(raw, str):
            try:
                return cls(UUID(raw))
            except ValueError:
                return None
        return None


allowed_kinds = _ALLOWED_KINDS