from __future__ import annotations

import csv
import io
import re
from datetime import datetime
from typing import Optional

from modules.transactions.application.ports import (
    ParsedImport,
    ParsedImportRow,
    TransactionFileParser,
    UnsupportedImportFormatError,
)


_AMOUNT_RE = re.compile(r"^-?\$?\s*([\d\.,]+)$")


def normalize_es_amount(raw: str) -> Optional[str]:
    """Convierte importe en formato ES (puntos como miles, coma decimal) a ISO.

    '$ 1.000.000,00' -> '1000000.00'
    '-$ 1.000.000,00' -> '-1000000.00'
    '97,52' -> '97.52'
    '-38.000,00' -> '-38000.00'
    Devuelve None si no puede parsear.
    """
    s = raw.strip().strip('"').strip()
    if not s:
        return None
    negative = s.startswith("-")
    if s.startswith("+") or s.startswith("-"):
        s = s[1:].strip()
    s = s.replace("$", "").strip()
    m = _AMOUNT_RE.match(f"{'-' if negative else ''}{s}")
    if m is None and not _AMOUNT_RE.match(s):
        return None
    digits = s
    if "," in digits:
        int_part, dec_part = digits.rsplit(",", 1)
        int_part = int_part.replace(".", "")
        digits = f"{int_part}.{dec_part}"
    else:
        digits = digits.replace(".", "")
    try:
        float(digits)
    except ValueError:
        return None
    return f"{'-' if negative else ''}{digits}"


def parse_es_date(raw: str, fmt: str) -> Optional[str]:
    """Convierte fecha en formato ES a ISO YYYY-MM-DD. Devuelve None si falla."""
    try:
        return datetime.strptime(raw.strip(), fmt).date().isoformat()
    except ValueError:
        return None


class MacroParser(TransactionFileParser):
    name = "macro"
    HEADER_TOKENS = ("Fecha", "Nro. Transacción", "Descripción", "Importe", "Saldo")
    DATE_FORMAT = "%d/%m/%Y"

    @classmethod
    def matches(cls, raw: bytes) -> bool:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            return False
        for line in text.splitlines()[:6]:
            stripped = line.strip()
            if stripped and all(token in stripped for token in cls.HEADER_TOKENS):
                return True
        return False

    def parse(self, raw: bytes, filename: str) -> ParsedImport:
        if not self.matches(raw):
            raise UnsupportedImportFormatError(filename)
        text = raw.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        header_idx = 0
        for i, row in enumerate(rows[:6]):
            if (
                len(row) >= 5
                and row[0].strip() == "Fecha"
                and "Nro. Transacción" in row[1]
            ):
                header_idx = i
                break
        data_rows = rows[header_idx + 1 :]
        parsed_rows: list[ParsedImportRow] = []
        for offset, row in enumerate(data_rows, start=header_idx + 2):
            if len(row) < 4:
                continue
            date_raw = row[0].strip()
            ext_ref = row[1].strip()
            description = row[2].strip()
            amount_raw = normalize_es_amount(row[3]) or row[3].strip()
            date_iso = parse_es_date(row[0].strip(), self.DATE_FORMAT) or row[0].strip()
            if not date_raw and not amount_raw:
                continue
            parsed_rows.append(
                ParsedImportRow(
                    raw_date=date_iso,
                    raw_amount=amount_raw,
                    description=description,
                    external_reference=ext_ref,
                    row_number=offset,
                )
            )
        return ParsedImport(source=self.name, rows=parsed_rows)


class MercadoPagoParser(TransactionFileParser):
    name = "mercado_pago"
    HEADER_TOKENS = (
        "RELEASE_DATE",
        "TRANSACTION_TYPE",
        "REFERENCE_ID",
        "TRANSACTION_NET_AMOUNT",
        "PARTIAL_BALANCE",
    )
    DATE_FORMAT = "%d-%m-%Y"

    @classmethod
    def matches(cls, raw: bytes) -> bool:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            return False
        for line in text.splitlines()[:10]:
            stripped = line.strip()
            if stripped and all(token in stripped for token in cls.HEADER_TOKENS):
                return True
        return False

    def parse(self, raw: bytes, filename: str) -> ParsedImport:
        if not self.matches(raw):
            raise UnsupportedImportFormatError(filename)
        text = raw.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text), delimiter=";")
        rows = list(reader)
        header_idx = 0
        for i, row in enumerate(rows[:10]):
            if (
                len(row) >= 5
                and row[0].strip() == "RELEASE_DATE"
                and row[1].strip() == "TRANSACTION_TYPE"
            ):
                header_idx = i
                break
        data_rows = rows[header_idx + 1 :]
        parsed_rows: list[ParsedImportRow] = []
        for offset, row in enumerate(data_rows, start=header_idx + 2):
            if len(row) < 4:
                continue
            date_raw = row[0].strip()
            description = row[1].strip()
            ext_ref = row[2].strip()
            amount_raw = normalize_es_amount(row[3]) or row[3].strip()
            date_iso = parse_es_date(row[0].strip(), self.DATE_FORMAT) or row[0].strip()
            if not date_raw and not amount_raw:
                continue
            parsed_rows.append(
                ParsedImportRow(
                    raw_date=date_iso,
                    raw_amount=amount_raw,
                    description=description,
                    external_reference=ext_ref,
                    row_number=offset,
                )
            )
        return ParsedImport(source=self.name, rows=parsed_rows)


_PARSERS = (MacroParser, MercadoPagoParser)


class AutoTransactionFileParser(TransactionFileParser):
    """Selector automático: elige el primer parser que coincida."""

    name = "auto"

    @classmethod
    def matches(cls, raw: bytes) -> bool:
        return any(p.matches(raw) for p in _PARSERS)

    def parse(self, raw: bytes, filename: str) -> ParsedImport:
        for parser_cls in _PARSERS:
            if parser_cls.matches(raw):
                return parser_cls().parse(raw, filename)
        raise UnsupportedImportFormatError(filename)