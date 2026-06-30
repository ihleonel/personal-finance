"""Unit tests for UpdateAccountUseCase."""

from __future__ import annotations

import unittest
from decimal import Decimal

from django.utils import translation

from modules.accounts.application.dtos import UpdateAccountInput
from modules.accounts.application.use_cases.update_account import UpdateAccountUseCase

from tests.fakes import InMemoryAccountRepository


class TestUpdateAccountUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryAccountRepository()
        self.use_case = UpdateAccountUseCase(repository=self.repo)
        self.account = self.repo.seed(
            owner_id=1, name="Efectivo", account_type="cash", currency="ARS"
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_updates_name(self) -> None:
        result = self.use_case.execute(
            owner_id=1, account_id=self.account.id, data=UpdateAccountInput(name="Cash ARS")
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.name, "Cash ARS")

    def test_updates_multiple_fields(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            data=UpdateAccountInput(
                name="Banco",
                account_type="bank",
                currency="USD",
                initial_balance="1000.00",
            ),
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.name, "Banco")
        self.assertEqual(out.account_type, "bank")
        self.assertEqual(out.currency, "USD")
        self.assertEqual(out.initial_balance, "1000.00")

    def test_partial_update_keeps_other_fields(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            data=UpdateAccountInput(name="Nuevo nombre"),
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.name, "Nuevo nombre")
        self.assertEqual(out.account_type, "cash")
        self.assertEqual(out.currency, "ARS")
        self.assertEqual(out.initial_balance, "0.00")

    def test_fails_when_account_not_owned(self) -> None:
        result = self.use_case.execute(
            owner_id=99, account_id=self.account.id, data=UpdateAccountInput(name="X")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "accounts.account.not_found")
        self.assertEqual(result.errors[0].message, "Cuenta no encontrada.")

    def test_fails_when_empty_payload(self) -> None:
        result = self.use_case.execute(
            owner_id=1, account_id=self.account.id, data=UpdateAccountInput()
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "accounts.account.empty_payload")
        self.assertEqual(
            result.errors[0].message, "Proporciona al menos un campo para actualizar."
        )

    def test_fails_when_account_inactive(self) -> None:
        self.repo.deactivate(self.account.id)
        result = self.use_case.execute(
            owner_id=1, account_id=self.account.id, data=UpdateAccountInput(name="X")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "accounts.account.inactive")
        self.assertEqual(
            result.errors[0].message,
            "La cuenta está inactiva y no se puede editar.",
        )

    def test_fails_when_name_blank(self) -> None:
        result = self.use_case.execute(
            owner_id=1, account_id=self.account.id, data=UpdateAccountInput(name="")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "name")
        self.assertEqual(result.errors[0].code, "accounts.name.required")
        self.assertEqual(result.errors[0].message, "El nombre de la cuenta es obligatorio.")

    def test_fails_when_name_already_exists_for_another_active(self) -> None:
        self.repo.seed(owner_id=1, name="Banco", account_type="bank", currency="USD")
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            data=UpdateAccountInput(name="Banco"),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "name")
        self.assertEqual(result.errors[0].code, "accounts.name.already_exists")
        self.assertEqual(
            result.errors[0].message, "Ya tenés una cuenta activa con ese nombre."
        )

    def test_allows_same_name_for_itself(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            data=UpdateAccountInput(name="Efectivo"),
        )
        self.assertTrue(result.is_success)

    def test_fails_when_currency_invalid(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            data=UpdateAccountInput(currency="JPY"),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "currency")
        self.assertEqual(result.errors[0].code, "accounts.currency.invalid")
        self.assertEqual(
            result.errors[0].message,
            "La moneda no es válida. Valores admitidos: ARS, USD, EUR.",
        )

    def test_fails_when_initial_balance_invalid(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            data=UpdateAccountInput(initial_balance="abc"),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "initial_balance")
        self.assertEqual(result.errors[0].code, "accounts.initial_balance.invalid")
        self.assertEqual(
            result.errors[0].message, "El saldo inicial debe ser un número válido."
        )

    def test_accepts_negative_initial_balance(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            account_id=self.account.id,
            data=UpdateAccountInput(initial_balance="-250.00"),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.initial_balance, "-250.00")