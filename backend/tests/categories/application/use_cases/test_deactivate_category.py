"""Unit tests for DeactivateCategoryUseCase."""

from __future__ import annotations

import unittest

from django.utils import translation

from modules.categories.application.use_cases.deactivate_category import DeactivateCategoryUseCase

from tests.fakes import InMemoryCategoryRepository


class TestDeactivateCategoryUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryCategoryRepository()
        self.use_case = DeactivateCategoryUseCase(repository=self.repo)
        self.category = self.repo.seed(owner_id=1, name="Comida", kind="expense")

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_deactivates_active_category(self) -> None:
        result = self.use_case.execute(owner_id=1, category_id=self.category.id)
        self.assertTrue(result.is_success)
        self.assertFalse(result.value.is_active)

    def test_fails_when_category_already_inactive(self) -> None:
        self.repo.deactivate(self.category.id)
        result = self.use_case.execute(owner_id=1, category_id=self.category.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categories.category.already_inactive")
        self.assertEqual(result.errors[0].message, "La categoría ya está inactiva.")

    def test_fails_when_category_not_owned(self) -> None:
        result = self.use_case.execute(owner_id=99, category_id=self.category.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categories.category.not_found")
        self.assertEqual(result.errors[0].message, "Categoría no encontrada.")

    def test_fails_when_category_does_not_exist(self) -> None:
        result = self.use_case.execute(owner_id=1, category_id=9999)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categories.category.not_found")
        self.assertEqual(result.errors[0].message, "Categoría no encontrada.")

    def test_deactivate_frees_name_for_reuse(self) -> None:
        first = self.use_case.execute(owner_id=1, category_id=self.category.id)
        self.assertTrue(first.is_success)

        reused = self.repo.exists_active_name_for_owner(1, "Comida")
        self.assertFalse(reused)