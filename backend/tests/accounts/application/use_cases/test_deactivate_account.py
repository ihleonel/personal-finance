"""Unit tests for DeactivateAccountUseCase."""

from __future__ import annotations

import unittest

from django.utils import translation

from modules.accounts.application.use_cases.deactivate_account import DeactivateAccountUseCase

from tests.fakes import InMemoryAccountRepository


class TestDeactivateAccountUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryAccountRepository()
        self.use_case = DeactivateAccountUseCase(repository=self.repo)
        self.account = self.repo.seed(owner_id=1, name="Efectivo", currency="ARS")

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_deactivates_active_account(self) -> None:
        result = self.use_case.execute(owner_id=1, account_id=self.account.id)
        self.assertTrue(result.is_success)
        self.assertFalse(result.value.is_active)

    def test_fails_when_account_already_inactive(self) -> None:
        self.repo.deactivate(self.account.id)
        result = self.use_case.execute(owner_id=1, account_id=self.account.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "accounts.account.already_inactive")
        self.assertEqual(result.errors[0].message, "La cuenta ya está inactiva.")

    def test_fails_when_account_not_owned(self) -> None:
        result = self.use_case.execute(owner_id=99, account_id=self.account.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "accounts.account.not_found")
        self.assertEqual(result.errors[0].message, "Cuenta no encontrada.")

    def test_fails_when_account_does_not_exist(self) -> None:
        result = self.use_case.execute(owner_id=1, account_id=9999)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "accounts.account.not_found")
        self.assertEqual(result.errors[0].message, "Cuenta no encontrada.")

    def test_deactivate_frees_name_for_reuse(self) -> None:
        first = self.use_case.execute(owner_id=1, account_id=self.account.id)
        self.assertTrue(first.is_success)

        reused = self.repo.exists_active_name_for_owner(1, "Efectivo")
        self.assertFalse(reused)