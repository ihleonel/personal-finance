"""Unit tests for UpdateUserProfileUseCase."""

from __future__ import annotations

import unittest

from django.utils import translation

from modules.auths.application.dtos import UpdateProfileInput
from modules.auths.application.use_cases.update_user_profile import UpdateUserProfileUseCase

from tests.fakes import InMemoryUserRepository


class TestUpdateUserProfileUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryUserRepository()
        self.use_case = UpdateUserProfileUseCase(repository=self.repo)
        self.user = self.repo.seed(
            email="alice@example.com",
            password_hash="hash",
            first_name="Alice",
            last_name="Liddell",
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_updates_first_name_only(self) -> None:
        result = self.use_case.execute(
            self.user.id, UpdateProfileInput(first_name="Alicia")
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.first_name, "Alicia")
        self.assertEqual(result.value.last_name, "Liddell")
        self.assertEqual(result.value.email, "alice@example.com")

    def test_updates_last_name_only(self) -> None:
        result = self.use_case.execute(
            self.user.id, UpdateProfileInput(last_name="Walker")
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.first_name, "Alice")
        self.assertEqual(result.value.last_name, "Walker")

    def test_updates_both_fields(self) -> None:
        result = self.use_case.execute(
            self.user.id,
            UpdateProfileInput(first_name="Alicia", last_name="Walker"),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.first_name, "Alicia")
        self.assertEqual(result.value.last_name, "Walker")

    def test_fails_when_user_not_found(self) -> None:
        result = self.use_case.execute(
            99999, UpdateProfileInput(first_name="x")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "non_field_errors")
        self.assertEqual(result.errors[0].code, "auth.user.not_found")
        self.assertEqual(result.errors[0].message, "Usuario no encontrado.")

    def test_persists_changes_in_repo(self) -> None:
        self.use_case.execute(self.user.id, UpdateProfileInput(first_name="Alicia"))
        refetched = self.repo.find_by_id(self.user.id)
        self.assertIsNotNone(refetched)
        self.assertEqual(refetched.first_name, "Alicia")
        self.assertEqual(refetched.last_name, "Liddell")

    def test_empty_payload_returns_error(self) -> None:
        result = self.use_case.execute(
            self.user.id, UpdateProfileInput(first_name="", last_name="")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "non_field_errors")
        self.assertEqual(result.errors[0].code, "auth.profile.empty_payload")
        self.assertEqual(
            result.errors[0].message,
            "Proporciona al menos uno de los campos: nombre o apellido.",
        )

    def test_oversized_field_returns_error(self) -> None:
        too_long = "a" * 200
        result = self.use_case.execute(
            self.user.id, UpdateProfileInput(first_name=too_long)
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "first_name")
        self.assertEqual(result.errors[0].code, "auth.field.max_length")
        self.assertEqual(
            result.errors[0].message,
            "Asegúrate de que este campo no tenga más de 150 caracteres.",
        )

    def test_accumulates_multiple_oversized_fields(self) -> None:
        too_long = "a" * 200
        result = self.use_case.execute(
            self.user.id,
            UpdateProfileInput(first_name=too_long, last_name=too_long),
        )
        self.assertFalse(result.is_success)
        fields = [e.field for e in result.errors]
        self.assertIn("first_name", fields)
        self.assertIn("last_name", fields)
        self.assertEqual(len(result.errors), 2)