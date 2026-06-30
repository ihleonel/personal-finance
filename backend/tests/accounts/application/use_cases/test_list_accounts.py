"""Unit tests for ListAccountsUseCase."""

from __future__ import annotations

import unittest
from decimal import Decimal

from django.utils import translation

from modules.accounts.application.use_cases.list_accounts import ListAccountsUseCase

from tests.fakes import InMemoryAccountRepository


class TestListAccountsUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryAccountRepository()
        self.use_case = ListAccountsUseCase(repository=self.repo)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_returns_empty_list_when_no_accounts(self) -> None:
        result = self.use_case.execute(owner_id=1)
        self.assertTrue(result.is_success)
        self.assertEqual(result.value, [])

    def test_returns_only_accounts_for_owner(self) -> None:
        self.repo.seed(owner_id=1, name="A", currency="ARS")
        self.repo.seed(owner_id=1, name="B", currency="USD")
        self.repo.seed(owner_id=2, name="C", currency="ARS")

        result = self.use_case.execute(owner_id=1)
        self.assertTrue(result.is_success)
        names = [a.name for a in result.value]
        self.assertEqual(sorted(names), ["A", "B"])

    def test_returns_active_and_inactive_with_flag(self) -> None:
        active = self.repo.seed(owner_id=1, name="A", currency="ARS")
        inactive = self.repo.seed(owner_id=1, name="B", currency="USD")
        self.repo.deactivate(inactive.id)

        result = self.use_case.execute(owner_id=1)
        self.assertTrue(result.is_success)
        by_name = {a.name: a.is_active for a in result.value}
        self.assertTrue(by_name["A"])
        self.assertFalse(by_name["B"])