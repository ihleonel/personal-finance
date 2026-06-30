"""Unit tests for GetCategoryUseCase."""

from __future__ import annotations

import unittest

from django.utils import translation

from modules.categories.application.use_cases.get_category import GetCategoryUseCase

from tests.fakes import InMemoryCategoryRepository


class TestGetCategoryUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryCategoryRepository()
        self.use_case = GetCategoryUseCase(repository=self.repo)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_returns_category_when_owned_by_user(self) -> None:
        category = self.repo.seed(owner_id=1, name="Salario", kind="income")
        result = self.use_case.execute(owner_id=1, category_id=category.id)
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.id, category.id)
        self.assertEqual(result.value.name, "Salario")

    def test_fails_when_category_does_not_exist(self) -> None:
        result = self.use_case.execute(owner_id=1, category_id=9999)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categories.category.not_found")
        self.assertEqual(result.errors[0].message, "Categoría no encontrada.")

    def test_fails_when_category_belongs_to_other_user(self) -> None:
        category = self.repo.seed(owner_id=2, name="Ajena", kind="income")
        result = self.use_case.execute(owner_id=1, category_id=category.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categories.category.not_found")
        self.assertEqual(result.errors[0].message, "Categoría no encontrada.")

    def test_returns_inactive_category_when_owned(self) -> None:
        category = self.repo.seed(owner_id=1, name="Inactiva", kind="expense")
        self.repo.deactivate(category.id)
        result = self.use_case.execute(owner_id=1, category_id=category.id)
        self.assertTrue(result.is_success)
        self.assertFalse(result.value.is_active)