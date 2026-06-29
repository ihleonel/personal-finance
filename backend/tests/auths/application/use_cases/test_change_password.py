"""Unit tests for ChangePasswordUseCase."""

from __future__ import annotations

import unittest

from django.contrib.auth.hashers import check_password, make_password
from django.utils import translation

from modules.auths.application.dtos import ChangePasswordInput
from modules.auths.application.use_cases.change_password import ChangePasswordUseCase

from tests.fakes import InMemoryUserRepository


_CURRENT_PASSWORD = "OldStrong123!"
_NEW_PASSWORD = "NewStrong456!"


class TestChangePasswordUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryUserRepository()
        self.use_case = ChangePasswordUseCase(repository=self.repo)
        self.user = self.repo.seed(
            email="alice@example.com",
            password_hash=make_password(_CURRENT_PASSWORD),
            first_name="Alice",
            last_name="Liddell",
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_changes_password_successfully(self) -> None:
        result = self.use_case.execute(
            self.user.id,
            ChangePasswordInput(
                current_password=_CURRENT_PASSWORD,
                new_password=_NEW_PASSWORD,
            ),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value, "Contraseña actualizada.")

        stored_hash = self.repo.get_password_hash("alice@example.com")
        self.assertIsNotNone(stored_hash)
        self.assertTrue(check_password(_NEW_PASSWORD, stored_hash))
        self.assertFalse(check_password(_CURRENT_PASSWORD, stored_hash))

    def test_fails_when_user_not_found(self) -> None:
        result = self.use_case.execute(
            99999,
            ChangePasswordInput(
                current_password=_CURRENT_PASSWORD,
                new_password=_NEW_PASSWORD,
            ),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "non_field_errors")
        self.assertEqual(result.errors[0].code, "auth.user.not_found")
        self.assertEqual(result.errors[0].message, "Usuario no encontrado.")

    def test_fails_when_current_password_missing(self) -> None:
        result = self.use_case.execute(
            self.user.id,
            ChangePasswordInput(current_password="", new_password=_NEW_PASSWORD),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "current_password")
        self.assertEqual(result.errors[0].code, "auth.password.required")
        self.assertEqual(
            result.errors[0].message, "La contraseña actual es obligatoria."
        )

    def test_fails_when_new_password_missing(self) -> None:
        result = self.use_case.execute(
            self.user.id,
            ChangePasswordInput(
                current_password=_CURRENT_PASSWORD,
                new_password="",
            ),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "new_password")
        self.assertEqual(result.errors[0].code, "auth.password.required")
        self.assertEqual(
            result.errors[0].message, "La nueva contraseña es obligatoria."
        )

    def test_fails_when_new_password_too_short(self) -> None:
        result = self.use_case.execute(
            self.user.id,
            ChangePasswordInput(
                current_password=_CURRENT_PASSWORD,
                new_password="short",
            ),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "new_password")
        self.assertEqual(result.errors[0].code, "auth.password.too_short")
        self.assertEqual(
            result.errors[0].message,
            "La contraseña debe tener al menos 8 caracteres.",
        )

    def test_fails_when_current_password_is_incorrect(self) -> None:
        result = self.use_case.execute(
            self.user.id,
            ChangePasswordInput(
                current_password="WrongPassword!",
                new_password=_NEW_PASSWORD,
            ),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "current_password")
        self.assertEqual(result.errors[0].code, "auth.password.invalid_credentials")
        self.assertEqual(
            result.errors[0].message, "La contraseña actual es incorrecta."
        )

    def test_fails_when_new_password_equals_current(self) -> None:
        result = self.use_case.execute(
            self.user.id,
            ChangePasswordInput(
                current_password=_CURRENT_PASSWORD,
                new_password=_CURRENT_PASSWORD,
            ),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "new_password")
        self.assertEqual(result.errors[0].code, "auth.password.same_password")
        self.assertEqual(
            result.errors[0].message,
            "La nueva contraseña no puede ser igual a la contraseña actual.",
        )

    def test_accumulates_current_and_new_password_errors(self) -> None:
        result = self.use_case.execute(
            self.user.id,
            ChangePasswordInput(current_password="", new_password="x"),
        )
        self.assertFalse(result.is_success)
        fields = [e.field for e in result.errors]
        codes = [e.code for e in result.errors]
        self.assertIn("current_password", fields)
        self.assertIn("new_password", fields)
        self.assertIn("auth.password.required", codes)
        self.assertIn("auth.password.too_short", codes)
        self.assertEqual(len(result.errors), 2)

    def test_does_not_update_password_when_current_password_is_wrong(self) -> None:
        original_hash = self.repo.get_password_hash("alice@example.com")
        self.use_case.execute(
            self.user.id,
            ChangePasswordInput(
                current_password="WrongPassword!",
                new_password=_NEW_PASSWORD,
            ),
        )
        self.assertEqual(
            self.repo.get_password_hash("alice@example.com"), original_hash
        )

    def test_does_not_update_password_when_new_equals_current(self) -> None:
        original_hash = self.repo.get_password_hash("alice@example.com")
        self.use_case.execute(
            self.user.id,
            ChangePasswordInput(
                current_password=_CURRENT_PASSWORD,
                new_password=_CURRENT_PASSWORD,
            ),
        )
        self.assertEqual(
            self.repo.get_password_hash("alice@example.com"), original_hash
        )