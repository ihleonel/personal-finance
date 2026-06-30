"""Unit tests for CreateAccountUseCase."""

from __future__ import annotations

import unittest
from decimal import Decimal

from django.utils import translation

from modules.accounts.application.dtos import CreateAccountInput
from modules.accounts.application.use_cases.create_account import CreateAccountUseCase

from tests.fakes import InMemoryAccountRepository


class TestCreateAccountUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryAccountRepository()
        self.use_case = CreateAccountUseCase(repository=self.repo)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_creates_account_with_defaults(self) -> None:
        result = self.use_case.execute(
            CreateAccountInput(
                owner_id=1, name="Efectivo", account_type="cash", currency="ARS"
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.owner_id, 1)
        self.assertEqual(out.name, "Efectivo")
        self.assertEqual(out.account_type, "cash")
        self.assertEqual(out.currency, "ARS")
        self.assertEqual(out.initial_balance, "0.00")
        self.assertTrue(out.is_active)

    def test_creates_account_with_initial_balance(self) -> None:
        result = self.use_case.execute(
            CreateAccountInput(
                owner_id=1,
                name="Banco",
                account_type="bank",
                currency="USD",
                initial_balance="1234.56",
            )
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.initial_balance, "1234.56")

    def test_accepts_negative_initial_balance(self) -> None:
        result = self.use_case.execute(
            CreateAccountInput(
                owner_id=1,
                name="Tarjeta",
                account_type="credit_card",
                currency="ARS",
                initial_balance="-500.00",
            )
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.initial_balance, "-500.00")

    def test_fails_when_name_missing(self) -> None:
        result = self.use_case.execute(
            CreateAccountInput(
                owner_id=1, name="", account_type="cash", currency="ARS"
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "name")
        self.assertEqual(result.errors[0].code, "accounts.name.required")
        self.assertEqual(result.errors[0].message, "El nombre de la cuenta es obligatorio.")

    def test_fails_when_name_too_long(self) -> None:
        result = self.use_case.execute(
            CreateAccountInput(
                owner_id=1,
                name="x" * 101,
                account_type="cash",
                currency="ARS",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "name")
        self.assertEqual(result.errors[0].code, "accounts.name.max_length")
        self.assertEqual(
            result.errors[0].message,
            "Asegúrate de que el nombre no tenga más de 100 caracteres.",
        )

    def test_fails_when_currency_invalid(self) -> None:
        result = self.use_case.execute(
            CreateAccountInput(
                owner_id=1, name="Cuenta", account_type="cash", currency="JPY"
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "currency")
        self.assertEqual(result.errors[0].code, "accounts.currency.invalid")
        self.assertEqual(
            result.errors[0].message,
            "La moneda no es válida. Valores admitidos: ARS, USD, EUR.",
        )

    def test_fails_when_account_type_invalid(self) -> None:
        result = self.use_case.execute(
            CreateAccountInput(
                owner_id=1, name="Cuenta", account_type="crypto", currency="ARS"
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "account_type")
        self.assertEqual(result.errors[0].code, "accounts.account_type.invalid")
        self.assertEqual(result.errors[0].message, "El tipo de cuenta no es válido.")

    def test_fails_when_initial_balance_not_numeric(self) -> None:
        result = self.use_case.execute(
            CreateAccountInput(
                owner_id=1,
                name="Cuenta",
                account_type="cash",
                currency="ARS",
                initial_balance="not-a-number",
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "initial_balance")
        self.assertEqual(result.errors[0].code, "accounts.initial_balance.invalid")
        self.assertEqual(
            result.errors[0].message, "El saldo inicial debe ser un número válido."
        )

    def test_fails_when_name_already_exists_for_owner(self) -> None:
        first = self.use_case.execute(
            CreateAccountInput(
                owner_id=1, name="Efectivo", account_type="cash", currency="ARS"
            )
        )
        self.assertTrue(first.is_success)

        second = self.use_case.execute(
            CreateAccountInput(
                owner_id=1, name="Efectivo", account_type="bank", currency="USD"
            )
        )
        self.assertFalse(second.is_success)
        self.assertEqual(second.errors[0].field, "name")
        self.assertEqual(second.errors[0].code, "accounts.name.already_exists")
        self.assertEqual(
            second.errors[0].message, "Ya tenés una cuenta activa con ese nombre."
        )

    def test_allows_same_name_for_different_owners(self) -> None:
        first = self.use_case.execute(
            CreateAccountInput(
                owner_id=1, name="Efectivo", account_type="cash", currency="ARS"
            )
        )
        self.assertTrue(first.is_success)

        second = self.use_case.execute(
            CreateAccountInput(
                owner_id=2, name="Efectivo", account_type="cash", currency="ARS"
            )
        )
        self.assertTrue(second.is_success)

    def test_allows_same_name_when_previous_is_inactive(self) -> None:
        first = self.use_case.execute(
            CreateAccountInput(
                owner_id=1, name="Efectivo", account_type="cash", currency="ARS"
            )
        )
        self.assertTrue(first.is_success)
        self.repo.deactivate(first.value.id)

        second = self.use_case.execute(
            CreateAccountInput(
                owner_id=1, name="Efectivo", account_type="bank", currency="USD"
            )
        )
        self.assertTrue(second.is_success)

    def test_does_not_persist_when_validation_fails(self) -> None:
        failed = self.use_case.execute(
            CreateAccountInput(
                owner_id=1, name="", account_type="cash", currency="ARS"
            )
        )
        self.assertFalse(failed.is_success)
        self.assertEqual(self.repo.list_by_owner(1), [])

    def test_accumulates_multiple_errors(self) -> None:
        result = self.use_case.execute(
            CreateAccountInput(
                owner_id=1, name="", account_type="crypto", currency="JPY"
            )
        )
        self.assertFalse(result.is_success)
        fields = [e.field for e in result.errors]
        self.assertIn("name", fields)
        self.assertIn("account_type", fields)
        self.assertIn("currency", fields)
        self.assertEqual(len(result.errors), 3)