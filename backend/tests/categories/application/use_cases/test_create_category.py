"""Unit tests for CreateCategoryUseCase."""

from __future__ import annotations

import unittest

from django.utils import translation

from modules.categories.application.dtos import CreateCategoryInput
from modules.categories.application.use_cases.create_category import CreateCategoryUseCase

from tests.fakes import InMemoryCategoryRepository


class TestCreateCategoryUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryCategoryRepository()
        self.use_case = CreateCategoryUseCase(repository=self.repo)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_creates_income_category(self) -> None:
        result = self.use_case.execute(
            CreateCategoryInput(owner_id=1, name="Salario", kind="income")
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.owner_id, 1)
        self.assertEqual(out.name, "Salario")
        self.assertEqual(out.kind, "income")
        self.assertTrue(out.is_active)

    def test_creates_expense_category(self) -> None:
        result = self.use_case.execute(
            CreateCategoryInput(owner_id=1, name="Comida", kind="expense")
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.kind, "expense")

    def test_fails_when_name_missing(self) -> None:
        result = self.use_case.execute(
            CreateCategoryInput(owner_id=1, name="", kind="expense")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "name")
        self.assertEqual(result.errors[0].code, "categories.name.required")
        self.assertEqual(
            result.errors[0].message, "El nombre de la categoría es obligatorio."
        )

    def test_fails_when_name_too_long(self) -> None:
        result = self.use_case.execute(
            CreateCategoryInput(owner_id=1, name="x" * 101, kind="expense")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "name")
        self.assertEqual(result.errors[0].code, "categories.name.max_length")
        self.assertEqual(
            result.errors[0].message,
            "Asegúrate de que el nombre no tenga más de 100 caracteres.",
        )

    def test_fails_when_kind_invalid(self) -> None:
        result = self.use_case.execute(
            CreateCategoryInput(owner_id=1, name="Categoría", kind="savings")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "kind")
        self.assertEqual(result.errors[0].code, "categories.kind.invalid")
        self.assertEqual(
            result.errors[0].message,
            "El tipo de categoría no es válido. Valores admitidos: income, expense.",
        )

    def test_fails_when_name_already_exists_for_owner(self) -> None:
        first = self.use_case.execute(
            CreateCategoryInput(owner_id=1, name="Comida", kind="expense")
        )
        self.assertTrue(first.is_success)

        second = self.use_case.execute(
            CreateCategoryInput(owner_id=1, name="Comida", kind="income")
        )
        self.assertFalse(second.is_success)
        self.assertEqual(second.errors[0].field, "name")
        self.assertEqual(second.errors[0].code, "categories.name.already_exists")
        self.assertEqual(
            second.errors[0].message,
            "Ya tenés una categoría activa con ese nombre.",
        )

    def test_allows_same_name_for_different_owners(self) -> None:
        first = self.use_case.execute(
            CreateCategoryInput(owner_id=1, name="Comida", kind="expense")
        )
        self.assertTrue(first.is_success)

        second = self.use_case.execute(
            CreateCategoryInput(owner_id=2, name="Comida", kind="expense")
        )
        self.assertTrue(second.is_success)

    def test_allows_same_name_when_previous_is_inactive(self) -> None:
        first = self.use_case.execute(
            CreateCategoryInput(owner_id=1, name="Comida", kind="expense")
        )
        self.assertTrue(first.is_success)
        self.repo.deactivate(first.value.id)

        second = self.use_case.execute(
            CreateCategoryInput(owner_id=1, name="Comida", kind="income")
        )
        self.assertTrue(second.is_success)

    def test_does_not_persist_when_validation_fails(self) -> None:
        failed = self.use_case.execute(
            CreateCategoryInput(owner_id=1, name="", kind="expense")
        )
        self.assertFalse(failed.is_success)
        self.assertEqual(self.repo.list_by_owner(1), [])

    def test_accumulates_multiple_errors(self) -> None:
        result = self.use_case.execute(
            CreateCategoryInput(owner_id=1, name="", kind="savings")
        )
        self.assertFalse(result.is_success)
        fields = [e.field for e in result.errors]
        self.assertIn("name", fields)
        self.assertIn("kind", fields)
        self.assertEqual(len(result.errors), 2)