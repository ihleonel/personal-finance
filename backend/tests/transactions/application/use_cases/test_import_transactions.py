"""Unit tests for ImportTransactionsUseCase using fixtures."""

from __future__ import annotations

import pathlib
import unittest
from datetime import date
from decimal import Decimal

from django.utils import translation

from modules.transactions.application.use_cases.import_transactions import (
    ImportTransactionsUseCase,
)
from modules.transactions.infrastructure.importers.parsers import (
    AutoTransactionFileParser,
    MacroParser,
    MercadoPagoParser,
)

from tests.fakes import (
    InMemoryAccountRepository,
    InMemoryTransactionRepository,
)


FIXTURES = pathlib.Path(__file__).parent.parent.parent / "fixtures"


def _read(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


class TestImportTransactionsUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.tx_repo = InMemoryTransactionRepository()
        self.account_repo = InMemoryAccountRepository()
        self.use_case = ImportTransactionsUseCase(
            repository=self.tx_repo,
            account_repository=self.account_repo,
        )
        self.account = self.account_repo.seed(owner_id=1, name="Cuenta")

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_imports_macro_csv_creates_all_valid_rows(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.summary.total, 67)
        self.assertEqual(out.summary.created, 67)
        self.assertEqual(out.summary.skipped, 0)
        self.assertEqual(out.summary.errors, 0)
        self.assertEqual(len(out.created), 67)

    def test_imports_mercado_pago_csv_creates_all_valid_rows(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_mercado_pago.csv"),
            filename="report_mercado_pago.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertGreater(out.summary.total, 50)
        self.assertEqual(out.summary.created, out.summary.total)
        self.assertEqual(out.summary.errors, 0)
        self.assertEqual(out.summary.skipped, 0)

    def test_dedup_skips_already_imported_rows(self) -> None:
        first = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(first.is_success)
        created_before = first.value.summary.created

        second = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(second.is_success)
        self.assertEqual(second.value.summary.created, 0)
        self.assertEqual(second.value.summary.skipped, created_before)
        self.assertEqual(second.value.summary.errors, 0)
        self.assertEqual(len(second.value.skipped), created_before)

    def test_dedup_only_same_account_and_source(self) -> None:
        self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        other_account = self.account_repo.seed(owner_id=1, name="Otra")
        result = self.use_case.execute(
            owner_id=1,
            account_id=other_account.id,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.summary.created, 67)
        self.assertEqual(result.value.summary.skipped, 0)

    def test_dedup_does_not_match_manual_transactions(self) -> None:
        self.tx_repo.seed(
            owner_id=1,
            account_id=self.account.id,
            kind="expense",
            amount=Decimal("1000.00"),
            date=date(2026, 4, 1),
            description="manual",
        )
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.summary.skipped, 0)

    def test_expense_kind_for_negative_amount_income_for_positive(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(result.is_success)
        kinds = {tx.kind for tx in result.value.created}
        self.assertEqual(kinds, {"income", "expense"})

    def test_amounts_are_positive_after_normalization(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_mercado_pago.csv"),
            filename="report_mercado_pago.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(result.is_success)
        for tx in result.value.created:
            self.assertGreater(Decimal(tx.amount), Decimal("0"))

    def test_persists_source_and_external_reference(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_mercado_pago.csv"),
            filename="report_mercado_pago.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(result.is_success)
        sources = {tx for tx in self.tx_repo._by_id.values()}
        for tx in self.tx_repo._by_id.values():
            if tx.source:
                self.assertEqual(tx.source, "mercado_pago")
                self.assertTrue(tx.external_reference)
        self.assertEqual(
            len({tx.external_reference for tx in self.tx_repo._by_id.values()}),
            result.value.summary.created,
        )

    def test_unsupported_format_returns_format_error(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_unsupported.csv"),
            filename="report_unsupported.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "file")
        self.assertEqual(result.errors[0].code, "import.format.unsupported")

    def test_account_not_found_fails(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=9999,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "account")
        self.assertEqual(result.errors[0].code, "transactions.account.not_found")

    def test_account_belongs_to_other_user_fails(self) -> None:
        other_account = self.account_repo.seed(owner_id=2, name="Ajena")
        result = self.use_case.execute(
            owner_id=1,
            account_id=other_account.id,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.account.not_found")

    def test_does_not_persist_when_account_invalid(self) -> None:
        self.use_case.execute(
            owner_id=1,
            account_id=9999,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertEqual(self.tx_repo.list_by_owner(1), [])

    def test_returns_summary_counts(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_mercado_pago.csv"),
            filename="report_mercado_pago.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(result.is_success)
        s = result.value.summary
        self.assertEqual(s.total, s.created + s.skipped + s.errors)


class TestImportTransactionsUseCaseWithCorruptedRows(unittest.TestCase):
    """Filas inválidas van a errors y el resto se persiste."""

    def setUp(self) -> None:
        translation.activate("es")
        self.tx_repo = InMemoryTransactionRepository()
        self.account_repo = InMemoryAccountRepository()
        self.use_case = ImportTransactionsUseCase(
            repository=self.tx_repo,
            account_repository=self.account_repo,
        )
        self.account = self.account_repo.seed(owner_id=1, name="Cuenta")

    def tearDown(self) -> None:
        translation.deactivate_all()

    def _make_macro_csv(self, body: str) -> bytes:
        header = (
            "Últimos movimientos de CUENTA SUELDO / DE LA SEGURIDAD SOCIAL,,,,\n"
            "Número de cuenta 410009499297447,,,,\n"
            "Fecha,Nro. Transacción,Descripción,Importe,Saldo\n"
        )
        return (header + body).encode("utf-8")

    def test_invalid_amount_row_goes_to_errors_others_persisted(self) -> None:
        body = (
            '01/04/2026,748143,EGRESO,"no-es-un-monto","$ 734.985,35"\n'
            '01/04/2026,2,OUTSOURCE,"$ 500.000,00","$ 1.734.985,35"\n'
        )
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=self._make_macro_csv(body),
            filename="macro.csv",
            parser=MacroParser(),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.summary.created, 1)
        self.assertEqual(result.value.summary.errors, 1)
        self.assertEqual(len(result.value.errors), 1)
        self.assertEqual(result.value.errors[0].field, "amount")

    def test_future_date_row_goes_to_errors(self) -> None:
        body = '2999-12-31,1,FUTURO,"$ 100,00","$ 0,00"\n'
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=self._make_macro_csv(body),
            filename="macro.csv",
            parser=MacroParser(),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.summary.errors, 1)
        self.assertEqual(result.value.errors[0].field, "date")

    def test_invalid_date_row_goes_to_errors(self) -> None:
        body = 'not-a-date,1,DESC,"$ 100,00","$ 0,00"\n'
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=self._make_macro_csv(body),
            filename="macro.csv",
            parser=MacroParser(),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.summary.errors, 1)
        self.assertEqual(result.value.errors[0].field, "date")

    def test_mercado_pago_explicit_parser_works(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_mercado_pago.csv"),
            filename="report_mercado_pago.csv",
            parser=MercadoPagoParser(),
        )
        self.assertTrue(result.is_success)
        self.assertGreater(result.value.summary.created, 0)
        self.assertEqual(result.value.summary.errors, 0)


if __name__ == "__main__":
    unittest.main()