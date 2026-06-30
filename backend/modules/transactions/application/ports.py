from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class ParsedImportRow:
    raw_date: str
    raw_amount: str
    description: str
    external_reference: str
    row_number: int


@dataclass(frozen=True)
class ParsedImport:
    source: str
    rows: list[ParsedImportRow] = field(default_factory=list)


class UnsupportedImportFormatError(Exception):
    pass


class TransactionFileParser(ABC):
    """Port: parsea bytes de un archivo CSV a ParsedImport. Implementado en infrastructure."""

    name: str

    @classmethod
    @abstractmethod
    def matches(cls, raw: bytes) -> bool: ...

    @abstractmethod
    def parse(self, raw: bytes, filename: str) -> ParsedImport: ...