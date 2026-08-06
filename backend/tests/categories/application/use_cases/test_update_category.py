"""Unit tests for UpdateCategoryUseCase."""

from __future__ import annotations

import unittest

from django.utils import translation

from modules.categories.application.dtos import UpdateCategoryInput
from modules.categories.application.use_cases.update_category import UpdateCategoryUseCase

from tests.fakes import InMemoryCategoryRepository


class TestUpdateCategoryUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryCategoryRepository()
        self.use_case = UpdateCategoryUseCase(repository=self.repo)
        self.category = self.repo.seed(owner_id=1, name="Comida", kind="expense")

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_updates_name(self) -> None:
        result = self.use_case.execute(
            owner_id=1, category_id=self.category.id, data=UpdateCategoryInput(name="Alimentos")
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.name, "Alimentos")

    def test_updates_kind(self) -> None:
        result = self.use_case.execute(
            owner_id=1, category_id=self.category.id, data=UpdateCategoryInput(kind="income")
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.kind, "income")

    def test_updates_is_fixed(self) -> None:
        result = self.use_case.execute(
            owner_id=1, category_id=self.category.id, data=UpdateCategoryInput(is_fixed=True)
        )
        self.assertTrue(result.is_success)
        self.assertTrue(result.value.is_fixed)

    def test_partial_update_keeps_is_fixed(self) -> None:
        fixed = self.repo.seed(owner_id=1, name="Alquiler", kind="expense", is_fixed=True)
        result = self.use_case.execute(
            owner_id=1,
            category_id=fixed.id,
            data=UpdateCategoryInput(name="Alquiler mensual"),
        )
        self.assertTrue(result.is_success)
        self.assertTrue(result.value.is_fixed)

    def test_updates_multiple_fields(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            category_id=self.category.id,
            data=UpdateCategoryInput(name="Sueldo", kind="income"),
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.name, "Sueldo")
        self.assertEqual(out.kind, "income")

    def test_partial_update_keeps_other_fields(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            category_id=self.category.id,
            data=UpdateCategoryInput(name="Nuevo nombre"),
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.name, "Nuevo nombre")
        self.assertEqual(out.kind, "expense")

    def test_fails_when_category_not_owned(self) -> None:
        result = self.use_case.execute(
            owner_id=99, category_id=self.category.id, data=UpdateCategoryInput(name="X")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categories.category.not_found")
        self.assertEqual(result.errors[0].message, "Categoría no encontrada.")

    def test_fails_when_empty_payload(self) -> None:
        result = self.use_case.execute(
            owner_id=1, category_id=self.category.id, data=UpdateCategoryInput()
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categories.category.empty_payload")
        self.assertEqual(
            result.errors[0].message, "Proporciona al menos un campo para actualizar."
        )

    def test_fails_when_category_inactive(self) -> None:
        self.repo.deactivate(self.category.id)
        result = self.use_case.execute(
            owner_id=1, category_id=self.category.id, data=UpdateCategoryInput(name="X")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categories.category.inactive")
        self.assertEqual(
            result.errors[0].message,
            "La categoría está inactiva y no se puede editar.",
        )

    def test_fails_when_name_blank(self) -> None:
        result = self.use_case.execute(
            owner_id=1, category_id=self.category.id, data=UpdateCategoryInput(name="")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "name")
        self.assertEqual(result.errors[0].code, "categories.name.required")
        self.assertEqual(
            result.errors[0].message, "El nombre de la categoría es obligatorio."
        )

    def test_fails_when_name_already_exists_for_another_active(self) -> None:
        self.repo.seed(owner_id=1, name="Sueldo", kind="income")
        result = self.use_case.execute(
            owner_id=1,
            category_id=self.category.id,
            data=UpdateCategoryInput(name="Sueldo"),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "name")
        self.assertEqual(result.errors[0].code, "categories.name.already_exists")
        self.assertEqual(
            result.errors[0].message,
            "Ya tenés una categoría activa con ese nombre.",
        )

    def test_allows_same_name_for_itself(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            category_id=self.category.id,
            data=UpdateCategoryInput(name="Comida"),
        )
        self.assertTrue(result.is_success)

    def test_fails_when_kind_invalid(self) -> None:
        result = self.use_case.execute(
            owner_id=1,
            category_id=self.category.id,
            data=UpdateCategoryInput(kind="savings"),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "kind")
        self.assertEqual(result.errors[0].code, "categories.kind.invalid")
        self.assertEqual(
            result.errors[0].message,
            "El tipo de categoría no es válido. Valores admitidos: income, expense.",
        )