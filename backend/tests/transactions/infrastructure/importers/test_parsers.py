"""Unit tests for CSV importers / parsers using fixtures."""

from __future__ import annotations

import pathlib
import unittest
from datetime import date

from modules.transactions.application.ports import UnsupportedImportFormatError
from modules.transactions.infrastructure.importers.parsers import (
    AutoTransactionFileParser,
    MacroParser,
    MercadoPagoParser,
    normalize_es_amount,
    parse_es_date,
)


FIXTURES = pathlib.Path(__file__).parent.parent.parent / "fixtures"


def _read(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


class TestNormalizeEsAmount(unittest.TestCase):
    def test_macro_positive_with_currency_and_thousands(self) -> None:
        self.assertEqual(normalize_es_amount("$ 1.000.000,00"), "1000000.00")

    def test_macro_negative_with_currency_and_thousands(self) -> None:
        self.assertEqual(normalize_es_amount("-$ 1.000.000,00"), "-1000000.00")

    def test_mercado_pago_positive(self) -> None:
        self.assertEqual(normalize_es_amount("97,52"), "97.52")

    def test_mercado_pago_negative_with_thousands(self) -> None:
        self.assertEqual(normalize_es_amount("-38.000,00"), "-38000.00")

    def test_quoted_value(self) -> None:
        self.assertEqual(normalize_es_amount('"$ 500.000,00"'), "500000.00")

    def test_invalid_returns_none(self) -> None:
        self.assertIsNone(normalize_es_amount("no-es-un-monto"))


class TestParseEsDate(unittest.TestCase):
    def test_macro_format(self) -> None:
        self.assertEqual(parse_es_date("01/04/2026", "%d/%m/%Y"), "2026-04-01")

    def test_mercado_pago_format(self) -> None:
        self.assertEqual(parse_es_date("02-03-2026", "%d-%m-%Y"), "2026-03-02")

    def test_invalid_returns_none(self) -> None:
        self.assertIsNone(parse_es_date("not-a-date", "%d/%m/%Y"))


class TestMacroParser(unittest.TestCase):
    def test_matches_real_report(self) -> None:
        self.assertTrue(MacroParser.matches(_read("report_macro.csv")))

    def test_does_not_match_mercado_pago(self) -> None:
        self.assertFalse(MacroParser.matches(_read("report_mercado_pago.csv")))

    def test_does_not_match_unsupported(self) -> None:
        self.assertFalse(MacroParser.matches(_read("report_unsupported.csv")))

    def test_parse_real_report_rows(self) -> None:
        parsed = MacroParser().parse(_read("report_macro.csv"), "report_macro.csv")
        self.assertEqual(parsed.source, "macro")
        self.assertEqual(len(parsed.rows), 67)

    def test_parse_first_row_fields(self) -> None:
        parsed = MacroParser().parse(_read("report_macro.csv"), "report_macro.csv")
        first = parsed.rows[0]
        self.assertEqual(first.raw_date, "2026-04-01")
        self.assertEqual(first.raw_amount, "-1000000.00")
        self.assertEqual(first.external_reference, "748143")
        self.assertTrue(first.description.startswith("EGRESO"))

    def test_parse_last_row_negative_balance(self) -> None:
        parsed = MacroParser().parse(_read("report_macro.csv"), "report_macro.csv")
        last = parsed.rows[-1]
        self.assertEqual(last.external_reference, "1090699588")
        self.assertEqual(last.raw_amount, "-539852.84")

    def test_parse_unsupported_raises(self) -> None:
        with self.assertRaises(UnsupportedImportFormatError):
            MacroParser().parse(_read("report_unsupported.csv"), "report_unsupported.csv")


class TestMercadoPagoParser(unittest.TestCase):
    def test_matches_real_report(self) -> None:
        self.assertTrue(MercadoPagoParser.matches(_read("report_mercado_pago.csv")))

    def test_does_not_match_macro(self) -> None:
        self.assertFalse(MercadoPagoParser.matches(_read("report_macro.csv")))

    def test_does_not_match_unsupported(self) -> None:
        self.assertFalse(MercadoPagoParser.matches(_read("report_unsupported.csv")))

    def test_parse_real_report_rows(self) -> None:
        parsed = MercadoPagoParser().parse(
            _read("report_mercado_pago.csv"), "report_mercado_pago.csv"
        )
        self.assertEqual(parsed.source, "mercado_pago")
        self.assertEqual(len(parsed.rows), 58)

    def test_parse_first_row_fields(self) -> None:
        parsed = MercadoPagoParser().parse(
            _read("report_mercado_pago.csv"), "report_mercado_pago.csv"
        )
        first = parsed.rows[0]
        self.assertEqual(first.raw_date, "2026-03-02")
        self.assertEqual(first.raw_amount, "97.52")
        self.assertEqual(first.external_reference, "1740431683971")
        self.assertIn("Rendimientos", first.description)

    def test_parse_negative_amount_row(self) -> None:
        parsed = MercadoPagoParser().parse(
            _read("report_mercado_pago.csv"), "report_mercado_pago.csv"
        )
        pago = next(r for r in parsed.rows if "EL ZORRITO" in r.description and r.raw_amount.startswith("-"))
        self.assertEqual(pago.raw_amount, "-38000.00")

    def test_parse_unsupported_raises(self) -> None:
        with self.assertRaises(UnsupportedImportFormatError):
            MercadoPagoParser().parse(_read("report_unsupported.csv"), "report_unsupported.csv")


class TestAutoTransactionFileParser(unittest.TestCase):
    def test_selects_macro(self) -> None:
        parsed = AutoTransactionFileParser().parse(
            _read("report_macro.csv"), "report_macro.csv"
        )
        self.assertEqual(parsed.source, "macro")

    def test_selects_mercado_pago(self) -> None:
        parsed = AutoTransactionFileParser().parse(
            _read("report_mercado_pago.csv"), "report_mercado_pago.csv"
        )
        self.assertEqual(parsed.source, "mercado_pago")

    def test_unsupported_raises(self) -> None:
        with self.assertRaises(UnsupportedImportFormatError):
            AutoTransactionFileParser().parse(
                _read("report_unsupported.csv"), "report_unsupported.csv"
            )

    def test_matches_macro(self) -> None:
        self.assertTrue(AutoTransactionFileParser.matches(_read("report_macro.csv")))

    def test_matches_mercado_pago(self) -> None:
        self.assertTrue(AutoTransactionFileParser.matches(_read("report_mercado_pago.csv")))

    def test_does_not_match_unsupported(self) -> None:
        self.assertFalse(AutoTransactionFileParser.matches(_read("report_unsupported.csv")))


if __name__ == "__main__":
    unittest.main()