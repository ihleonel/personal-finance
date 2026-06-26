"""Unit tests for RegisterUserUseCase."""

from __future__ import annotations

import unittest

from django.contrib.auth.hashers import check_password, identify_hasher
from django.utils import translation

from modules.auths.application.dtos import RegisterInput
from modules.auths.application.use_cases.register_user import RegisterUserUseCase

from tests.fakes import FakeTokenService, InMemoryUserRepository


class TestRegisterUserUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryUserRepository()
        self.tokens = FakeTokenService()
        self.use_case = RegisterUserUseCase(repository=self.repo, token_service=self.tokens)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_creates_user_and_returns_tokens(self) -> None:
        result = self.use_case.execute(
            RegisterInput(email="a@b.com", password="Strong123!", first_name="A", last_name="B")
        )

        self.assertTrue(result.is_success)
        self.assertTrue(self.repo.exists_by_email("a@b.com"))
        out = result.value
        self.assertEqual(out.user.email, "a@b.com")
        self.assertEqual(out.user.first_name, "A")
        self.assertEqual(out.user.last_name, "B")
        self.assertTrue(out.user.is_active)
        self.assertEqual(out.tokens.access, "fake-access-1")
        self.assertEqual(out.tokens.refresh, "fake-refresh-1")

    def test_hashes_password(self) -> None:
        result = self.use_case.execute(
            RegisterInput(email="a@b.com", password="Strong123!")
        )
        self.assertTrue(result.is_success)

        password_hash = self.repo.get_password_hash("a@b.com")
        self.assertIsNotNone(password_hash)
        self.assertNotEqual(password_hash, "Strong123!")
        self.assertTrue(check_password("Strong123!", password_hash))
        self.assertEqual(identify_hasher(password_hash).algorithm, "pbkdf2_sha256")

    def test_fails_when_email_already_exists(self) -> None:
        first = self.use_case.execute(
            RegisterInput(email="dup@b.com", password="Strong123!")
        )
        self.assertTrue(first.is_success)

        second = self.use_case.execute(
            RegisterInput(email="dup@b.com", password="OtherPass1!")
        )
        self.assertFalse(second.is_success)
        self.assertEqual(len(second.errors), 1)
        self.assertEqual(second.errors[0].field, "email")
        self.assertEqual(second.errors[0].code, "auth.email.already_exists")
        self.assertEqual(
            second.errors[0].message, "Este correo ya está registrado."
        )

    def test_email_match_is_case_insensitive_for_uniqueness(self) -> None:
        first = self.use_case.execute(
            RegisterInput(email="Foo@Bar.com", password="Strong123!")
        )
        self.assertTrue(first.is_success)

        second = self.use_case.execute(
            RegisterInput(email="foo@bar.com", password="OtherPass1!")
        )
        self.assertFalse(second.is_success)
        self.assertEqual(second.errors[0].field, "email")
        self.assertEqual(second.errors[0].code, "auth.email.already_exists")

    def test_fails_with_invalid_email(self) -> None:
        result = self.use_case.execute(
            RegisterInput(email="not-an-email", password="Strong123!")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "email")
        self.assertEqual(result.errors[0].code, "auth.email.invalid_format")
        self.assertEqual(
            result.errors[0].message, "Ingresa un correo electrónico válido."
        )

    def test_fails_when_password_missing(self) -> None:
        result = self.use_case.execute(RegisterInput(email="a@b.com", password=""))
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "password")
        self.assertEqual(result.errors[0].code, "auth.password.required")
        self.assertEqual(result.errors[0].message, "La contraseña es obligatoria.")

    def test_fails_when_password_too_short(self) -> None:
        result = self.use_case.execute(RegisterInput(email="a@b.com", password="short"))
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "password")
        self.assertEqual(result.errors[0].code, "auth.password.too_short")
        self.assertEqual(
            result.errors[0].message,
            "La contraseña debe tener al menos 8 caracteres.",
        )

    def test_accumulates_email_and_password_errors(self) -> None:
        result = self.use_case.execute(
            RegisterInput(email="not-an-email", password="x")
        )
        self.assertFalse(result.is_success)
        fields = [e.field for e in result.errors]
        codes = [e.code for e in result.errors]
        self.assertIn("email", fields)
        self.assertIn("password", fields)
        self.assertIn("auth.email.invalid_format", codes)
        self.assertIn("auth.password.too_short", codes)
        self.assertEqual(len(result.errors), 2)

    def test_accumulates_invalid_format_and_skips_uniqueness_check(self) -> None:
        # When email isn't parseable we skip the uniqueness lookup.
        self.use_case.execute(
            RegisterInput(email="dup@b.com", password="Strong123!")
        )
        result = self.use_case.execute(
            RegisterInput(email="not-an-email", password="Strong123!")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].code, "auth.email.invalid_format")

    def test_token_service_is_invoked_with_new_user_id(self) -> None:
        result = self.use_case.execute(
            RegisterInput(email="a@b.com", password="Strong123!")
        )
        self.assertTrue(result.is_success)
        self.assertEqual(self.tokens.generated, [result.value.user.id])

    def test_does_not_persist_user_when_validation_fails(self) -> None:
        self.use_case.execute(
            RegisterInput(email="dup@b.com", password="Strong123!")
        )
        failed = self.use_case.execute(
            RegisterInput(email="dup@b.com", password="OtherPass1!")
        )
        self.assertFalse(failed.is_success)
        # Only the original user is in the repo.
        self.assertEqual(len(self.tokens.generated), 1)