"""Unit tests for GetAccountUseCase."""

from __future__ import annotations

import unittest

from django.utils import translation

from modules.accounts.application.use_cases.get_account import GetAccountUseCase

from tests.fakes import InMemoryAccountRepository


class TestGetAccountUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryAccountRepository()
        self.use_case = GetAccountUseCase(repository=self.repo)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_returns_account_when_owned_by_user(self) -> None:
        account = self.repo.seed(owner_id=1, name="Efectivo", currency="ARS")
        result = self.use_case.execute(owner_id=1, account_id=account.id)
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.id, account.id)
        self.assertEqual(result.value.name, "Efectivo")

    def test_fails_when_account_does_not_exist(self) -> None:
        result = self.use_case.execute(owner_id=1, account_id=9999)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "accounts.account.not_found")
        self.assertEqual(result.errors[0].message, "Cuenta no encontrada.")

    def test_fails_when_account_belongs_to_other_user(self) -> None:
        account = self.repo.seed(owner_id=2, name="Ajena", currency="ARS")
        result = self.use_case.execute(owner_id=1, account_id=account.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "accounts.account.not_found")
        self.assertEqual(result.errors[0].message, "Cuenta no encontrada.")

    def test_returns_inactive_account_when_owned(self) -> None:
        account = self.repo.seed(owner_id=1, name="Inactiva", currency="ARS")
        self.repo.deactivate(account.id)
        result = self.use_case.execute(owner_id=1, account_id=account.id)
        self.assertTrue(result.is_success)
        self.assertFalse(result.value.is_active)