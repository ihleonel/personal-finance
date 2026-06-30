"""Unit tests for ListCategoriesUseCase."""

from __future__ import annotations

import unittest

from django.utils import translation

from modules.categories.application.use_cases.list_categories import ListCategoriesUseCase

from tests.fakes import InMemoryCategoryRepository


class TestListCategoriesUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryCategoryRepository()
        self.use_case = ListCategoriesUseCase(repository=self.repo)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_returns_empty_list_when_no_categories(self) -> None:
        result = self.use_case.execute(owner_id=1)
        self.assertTrue(result.is_success)
        self.assertEqual(result.value, [])

    def test_returns_only_categories_for_owner(self) -> None:
        self.repo.seed(owner_id=1, name="A", kind="income")
        self.repo.seed(owner_id=1, name="B", kind="expense")
        self.repo.seed(owner_id=2, name="C", kind="income")

        result = self.use_case.execute(owner_id=1)
        self.assertTrue(result.is_success)
        names = [c.name for c in result.value]
        self.assertEqual(sorted(names), ["A", "B"])

    def test_returns_active_and_inactive_with_flag(self) -> None:
        active = self.repo.seed(owner_id=1, name="A", kind="income")
        inactive = self.repo.seed(owner_id=1, name="B", kind="expense")
        self.repo.deactivate(inactive.id)

        result = self.use_case.execute(owner_id=1)
        self.assertTrue(result.is_success)
        by_name = {c.name: c.is_active for c in result.value}
        self.assertTrue(by_name["A"])
        self.assertFalse(by_name["B"])