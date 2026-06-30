"""Unit tests for ActivateAccountUseCase."""

from __future__ import annotations

import unittest

from django.utils import translation

from modules.accounts.application.use_cases.activate_account import ActivateAccountUseCase

from tests.fakes import InMemoryAccountRepository


class TestActivateAccountUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryAccountRepository()
        self.use_case = ActivateAccountUseCase(repository=self.repo)
        self.account = self.repo.seed(owner_id=1, name="Efectivo", currency="ARS")
        self.repo.deactivate(self.account.id)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_activates_inactive_account(self) -> None:
        result = self.use_case.execute(owner_id=1, account_id=self.account.id)
        self.assertTrue(result.is_success)
        self.assertTrue(result.value.is_active)

    def test_fails_when_account_already_active(self) -> None:
        self.repo.activate(self.account.id)
        result = self.use_case.execute(owner_id=1, account_id=self.account.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "accounts.account.already_active")
        self.assertEqual(result.errors[0].message, "La cuenta ya está activa.")

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

    def test_activate_reclaims_name(self) -> None:
        result = self.use_case.execute(owner_id=1, account_id=self.account.id)
        self.assertTrue(result.is_success)

        reclaimed = self.repo.exists_active_name_for_owner(1, "Efectivo")
        self.assertTrue(reclaimed)