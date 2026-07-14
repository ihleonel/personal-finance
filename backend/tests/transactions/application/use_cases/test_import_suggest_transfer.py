"""Unit tests for ImportTransactionsUseCase transfer detection integration."""

from __future__ import annotations

import pathlib
import unittest

from django.utils import translation

from modules.transactions.application.use_cases.import_transactions import (
    ImportTransactionsUseCase,
)
from modules.transactions.infrastructure.importers.parsers import (
    AutoTransactionFileParser,
)
from modules.transfer_detection.application.detector import (
    TransferCandidateDetector,
    TransferPairMatcher,
)

from tests.fakes import (
    InMemoryAccountRepository,
    InMemoryTransactionRepository,
    InMemoryTransferDetectionRuleRepository,
)


FIXTURES = pathlib.Path(__file__).parent.parent.parent / "fixtures"


def _read(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


class TestImportSuggestsTransferButDoesNotPersist(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.tx_repo = InMemoryTransactionRepository()
        self.account_repo = InMemoryAccountRepository()
        self.transfer_rule_repo = InMemoryTransferDetectionRuleRepository()
        self.transfer_rule_repo.seed(
            owner_id=1, pattern="transf", match_type="contains", priority=5
        )
        self.use_case = ImportTransactionsUseCase(
            repository=self.tx_repo,
            account_repository=self.account_repo,
            transfer_rule_repository=self.transfer_rule_repo,
            transfer_candidate_detector=TransferCandidateDetector(),
            transfer_pair_matcher=TransferPairMatcher(),
        )
        self.account = self.account_repo.seed(owner_id=1, name="Cuenta")

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_suggested_is_transfer_true_for_matching_rows(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(result.is_success)
        matching = [
            tx for tx in result.value.created if tx.suggested_is_transfer
        ]
        self.assertGreater(len(matching), 0)

    def test_transfer_group_id_remains_none_even_when_suggested(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            file_bytes=_read("report_macro.csv"),
            filename="report_macro.csv",
            parser=AutoTransactionFileParser(),
        )
        self.assertTrue(result.is_success)
        for tx in result.value.created:
            self.assertIsNone(tx.transfer_group_id)

    def test_no_transfer_rules_yields_false_suggestion(self) -> None:
        transfer_rule_repo = InMemoryTransferDetectionRuleRepository()
        use_case = ImportTransactionsUseCase(
            repository=self.tx_repo,
            account_repository=self.account_repo,
            transfer_rule_repository=transfer_rule_repo,
            transfer_candidate_detector=TransferCandidateDetector(),
            transfer_pair_matcher=TransferPairMatcher(),
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
            self.assertFalse(tx.suggested_is_transfer)

    def test_without_transfer_rule_repository_suggestions_are_false(self) -> None:
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
            self.assertFalse(tx.suggested_is_transfer)
            self.assertIsNone(tx.suggested_transfer_pair)


if __name__ == "__main__":
    unittest.main()