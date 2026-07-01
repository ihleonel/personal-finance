"""Unit tests for ImportTransactionsUseCase categorization suggestion integration."""

from __future__ import annotations

import pathlib
import unittest

from django.utils import translation

from modules.categorization_rules.application.categorizer import (
    CategorySuggestionService,
)
from modules.transactions.application.use_cases.import_transactions import (
    ImportTransactionsUseCase,
)
from modules.transactions.infrastructure.importers.parsers import (
    AutoTransactionFileParser,
)

from tests.fakes import (
    InMemoryAccountRepository,
    InMemoryCategorizationRuleRepository,
    InMemoryCategoryRepository,
    InMemoryTransactionRepository,
)


FIXTURES = pathlib.Path(__file__).parent.parent.parent / "fixtures"


def _read(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


class TestImportSuggestsCategoryButDoesNotAssign(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.tx_repo = InMemoryTransactionRepository()
        self.account_repo = InMemoryAccountRepository()
        self.category_repo = InMemoryCategoryRepository()
        self.rule_repo = InMemoryCategorizationRuleRepository()
        self.comida = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        # Una regla que matchea descripciones que contengan "outsource" (presente en macro.csv)
        self.rule_repo.seed(
            owner_id=1, pattern="outsource", match_type="contains",
            category_id=self.comida.id, priority=5,
        )
        self.use_case = ImportTransactionsUseCase(
            repository=self.tx_repo,
            account_repository=self.account_repo,
            rule_repository=self.rule_repo,
            suggestion_service=CategorySuggestionService(),
        )
        self.account = self.account_repo.seed(owner_id=1, name="Cuenta")

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_suggested_category_id_populated_for_matching_rows(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(result.is_success)
        matching = [
            tx for tx in result.value.created
            if tx.suggested_category_id == self.comida.id
        ]
        self.assertGreater(len(matching), 0)

    def test_category_id_remains_none_even_when_suggested(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(result.is_success)
        for tx in result.value.created:
            self.assertIsNone(tx.category_id)

    def test_no_rules_yields_none_suggestion(self) -> None:
        self.rule_repo = InMemoryCategorizationRuleRepository()
        use_case = ImportTransactionsUseCase(
            repository=self.tx_repo,
            account_repository=self.account_repo,
            rule_repository=self.rule_repo,
            suggestion_service=CategorySuggestionService(),
        )
        result = use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(result.is_success)
        for tx in result.value.created:
            self.assertIsNone(tx.suggested_category_id)

    def test_without_rule_repository_suggestions_are_none(self) -> None:
        use_case = ImportTransactionsUseCase(
            repository=self.tx_repo,
            account_repository=self.account_repo,
        )
        result = use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(result.is_success)
        for tx in result.value.created:
            self.assertIsNone(tx.suggested_category_id)


if __name__ == "__main__":
    unittest.main()