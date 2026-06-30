"""Unit tests for ActivateCategoryUseCase."""

from __future__ import annotations

import unittest

from django.utils import translation

from modules.categories.application.use_cases.activate_category import ActivateCategoryUseCase

from tests.fakes import InMemoryCategoryRepository


class TestActivateCategoryUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryCategoryRepository()
        self.use_case = ActivateCategoryUseCase(repository=self.repo)
        self.category = self.repo.seed(owner_id=1, name="Comida", kind="expense")
        self.repo.deactivate(self.category.id)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_activates_inactive_category(self) -> None:
        result = self.use_case.execute(owner_id=1, category_id=self.category.id)
        self.assertTrue(result.is_success)
        self.assertTrue(result.value.is_active)

    def test_fails_when_category_already_active(self) -> None:
        self.repo.activate(self.category.id)
        result = self.use_case.execute(owner_id=1, category_id=self.category.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categories.category.already_active")
        self.assertEqual(result.errors[0].message, "La categoría ya está activa.")

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

    def test_activate_reclaims_name(self) -> None:
        result = self.use_case.execute(owner_id=1, category_id=self.category.id)
        self.assertTrue(result.is_success)

        reclaimed = self.repo.exists_active_name_for_owner(1, "Comida")
        self.assertTrue(reclaimed)