"""Unit tests for LinkTransferUseCase."""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from django.utils import translation

from modules.transactions.application.dtos import LinkTransferInput
from modules.transactions.application.use_cases.link_transfer import (
    LinkTransferUseCase,
)

from tests.fakes import InMemoryTransactionRepository


class TestLinkTransferUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.tx_repo = InMemoryTransactionRepository()
        self.use_case = LinkTransferUseCase(repository=self.tx_repo)
        self.source_tx = self.tx_repo.seed(
            owner_id=1,
            account_id=10,
            kind="expense",
            amount=Decimal("500.00"),
            date=date(2026, 1, 15),
            description="Transferencia a ahorro",
        )
        self.destination_tx = self.tx_repo.seed(
            owner_id=1,
            account_id=20,
            kind="income",
            amount=Decimal("500.00"),
            date=date(2026, 1, 15),
            description="Transferencia recibida",
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_links_two_transactions_with_shared_group_id(self) -> None:
        result = self.use_case.execute(
            LinkTransferInput(
                owner_id=1,
                source_id=self.source_tx.id or 0,
                destination_id=self.destination_tx.id or 0,
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertIsNotNone(out.source.transfer_group_id)
        self.assertEqual(
            out.source.transfer_group_id, out.destination.transfer_group_id
        )

    def test_fails_when_source_not_found(self) -> None:
        result = self.use_case.execute(
            LinkTransferInput(owner_id=1, source_id=9999, destination_id=self.destination_tx.id or 0)
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transfer.not_found")

    def test_fails_when_destination_not_found(self) -> None:
        result = self.use_case.execute(
            LinkTransferInput(owner_id=1, source_id=self.source_tx.id or 0, destination_id=9999)
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transfer.not_found")

    def test_fails_when_not_owned(self) -> None:
        result = self.use_case.execute(
            LinkTransferInput(
                owner_id=2,
                source_id=self.source_tx.id or 0,
                destination_id=self.destination_tx.id or 0,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transfer.not_owned")

    def test_fails_when_already_linked(self) -> None:
        other_source = self.tx_repo.seed(
            owner_id=1,
            account_id=10,
            kind="expense",
            amount=Decimal("100.00"),
            date=date(2026, 2, 1),
        )
        other_destination = self.tx_repo.seed(
            owner_id=1,
            account_id=20,
            kind="income",
            amount=Decimal("100.00"),
            date=date(2026, 2, 1),
        )
        self.use_case.execute(
            LinkTransferInput(
                owner_id=1,
                source_id=other_source.id or 0,
                destination_id=other_destination.id or 0,
            )
        )
        result = self.use_case.execute(
            LinkTransferInput(
                owner_id=1,
                source_id=other_source.id or 0,
                destination_id=self.destination_tx.id or 0,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transfer.already_linked")

    def test_fails_when_same_account(self) -> None:
        same_account_income = self.tx_repo.seed(
            owner_id=1,
            account_id=10,
            kind="income",
            amount=Decimal("500.00"),
            date=date(2026, 1, 15),
        )
        result = self.use_case.execute(
            LinkTransferInput(
                owner_id=1,
                source_id=self.source_tx.id or 0,
                destination_id=same_account_income.id or 0,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transfer.same_account")

    def test_fails_when_invalid_kinds(self) -> None:
        other_expense = self.tx_repo.seed(
            owner_id=1,
            account_id=20,
            kind="expense",
            amount=Decimal("500.00"),
            date=date(2026, 1, 15),
        )
        result = self.use_case.execute(
            LinkTransferInput(
                owner_id=1,
                source_id=self.source_tx.id or 0,
                destination_id=other_expense.id or 0,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transfer.invalid_kinds")

    def test_fails_when_amount_mismatch(self) -> None:
        mismatch_income = self.tx_repo.seed(
            owner_id=1,
            account_id=20,
            kind="income",
            amount=Decimal("600.00"),
            date=date(2026, 1, 15),
        )
        result = self.use_case.execute(
            LinkTransferInput(
                owner_id=1,
                source_id=self.source_tx.id or 0,
                destination_id=mismatch_income.id or 0,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transfer.amount_mismatch")

    def test_does_not_link_when_validation_fails(self) -> None:
        result = self.use_case.execute(
            LinkTransferInput(owner_id=1, source_id=9999, destination_id=self.destination_tx.id or 0)
        )
        self.assertFalse(result.is_success)
        self.assertIsNone(self.tx_repo.find_by_id(self.source_tx.id or 0).transfer_group_id)
        self.assertIsNone(self.tx_repo.find_by_id(self.destination_tx.id or 0).transfer_group_id)