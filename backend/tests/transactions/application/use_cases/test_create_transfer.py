"""Unit tests for CreateTransferUseCase."""

from __future__ import annotations

import unittest

from django.utils import translation

from modules.transactions.application.dtos import CreateTransferInput
from modules.transactions.application.use_cases.create_transfer import (
    CreateTransferUseCase,
)

from tests.fakes import (
    InMemoryAccountRepository,
    InMemoryTransactionRepository,
)


class TestCreateTransferUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.tx_repo = InMemoryTransactionRepository()
        self.account_repo = InMemoryAccountRepository()
        self.use_case = CreateTransferUseCase(
            repository=self.tx_repo,
            account_repository=self.account_repo,
        )
        self.source = self.account_repo.seed(
            owner_id=1, name="Efectivo", currency="ARS"
        )
        self.destination = self.account_repo.seed(
            owner_id=1, name="Banco", currency="ARS"
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_creates_transfer_with_two_transactions(self) -> None:
        result = self.use_case.execute(
            CreateTransferInput(
                owner_id=1,
                source_account_id=self.source.id,
                destination_account_id=self.destination.id,
                amount="500.00",
                date="2026-01-15",
                description="Transferencia a ahorro",
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.source.kind, "expense")
        self.assertEqual(out.destination.kind, "income")
        self.assertEqual(out.source.account_id, self.source.id)
        self.assertEqual(out.destination.account_id, self.destination.id)
        self.assertEqual(out.source.amount, "500.00")
        self.assertEqual(out.destination.amount, "500.00")
        self.assertEqual(out.source.date, "2026-01-15")
        self.assertEqual(out.destination.date, "2026-01-15")
        self.assertEqual(out.source.description, "Transferencia a ahorro")
        self.assertIsNotNone(out.source.transfer_group_id)
        self.assertEqual(
            out.source.transfer_group_id, out.destination.transfer_group_id
        )

    def test_fails_when_same_account(self) -> None:
        result = self.use_case.execute(
            CreateTransferInput(
                owner_id=1,
                source_account_id=self.source.id,
                destination_account_id=self.source.id,
                amount="500.00",
                date="2026-01-15",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "transactions.transfer.same_account")

    def test_fails_when_source_not_owned(self) -> None:
        result = self.use_case.execute(
            CreateTransferInput(
                owner_id=1,
                source_account_id=9999,
                destination_account_id=self.destination.id,
                amount="500.00",
                date="2026-01-15",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "source_account")
        self.assertEqual(result.errors[0].code, "transactions.account.not_found")

    def test_fails_when_destination_not_owned(self) -> None:
        result = self.use_case.execute(
            CreateTransferInput(
                owner_id=1,
                source_account_id=self.source.id,
                destination_account_id=9999,
                amount="500.00",
                date="2026-01-15",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "destination_account")
        self.assertEqual(result.errors[0].code, "transactions.account.not_found")

    def test_fails_when_source_inactive(self) -> None:
        self.account_repo.deactivate(self.source.id)
        result = self.use_case.execute(
            CreateTransferInput(
                owner_id=1,
                source_account_id=self.source.id,
                destination_account_id=self.destination.id,
                amount="500.00",
                date="2026-01-15",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "source_account")
        self.assertEqual(result.errors[0].code, "transactions.account.inactive")

    def test_fails_when_destination_inactive(self) -> None:
        self.account_repo.deactivate(self.destination.id)
        result = self.use_case.execute(
            CreateTransferInput(
                owner_id=1,
                source_account_id=self.source.id,
                destination_account_id=self.destination.id,
                amount="500.00",
                date="2026-01-15",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "destination_account")
        self.assertEqual(result.errors[0].code, "transactions.account.inactive")

    def test_fails_when_amount_invalid(self) -> None:
        result = self.use_case.execute(
            CreateTransferInput(
                owner_id=1,
                source_account_id=self.source.id,
                destination_account_id=self.destination.id,
                amount="not-a-number",
                date="2026-01-15",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "amount")
        self.assertEqual(result.errors[0].code, "transactions.amount.invalid")

    def test_fails_when_date_in_future(self) -> None:
        result = self.use_case.execute(
            CreateTransferInput(
                owner_id=1,
                source_account_id=self.source.id,
                destination_account_id=self.destination.id,
                amount="500.00",
                date="2999-12-31",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "date")
        self.assertEqual(result.errors[0].code, "transactions.date.invalid")

    def test_does_not_persist_when_validation_fails(self) -> None:
        result = self.use_case.execute(
            CreateTransferInput(
                owner_id=1,
                source_account_id=self.source.id,
                destination_account_id=self.destination.id,
                amount="not-a-number",
                date="2026-01-15",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(self.tx_repo.list_by_owner(1), [])