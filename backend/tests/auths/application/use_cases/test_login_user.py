"""Unit tests for LoginUserUseCase."""

from __future__ import annotations

import unittest

from django.contrib.auth.hashers import make_password
from django.utils import translation

from modules.auths.application.dtos import LoginInput
from modules.auths.application.use_cases.login_user import LoginUserUseCase

from tests.fakes import FakeTokenService, InMemoryUserRepository


class TestLoginUserUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryUserRepository()
        self.tokens = FakeTokenService()
        self.repo.seed(
            email="alice@example.com",
            password_hash=make_password("CorrectPass1!"),
            first_name="Alice",
            last_name="Liddell",
            is_active=True,
        )
        self.use_case = LoginUserUseCase(repository=self.repo, token_service=self.tokens)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_returns_tokens_for_valid_credentials(self) -> None:
        result = self.use_case.execute(
            LoginInput(email="alice@example.com", password="CorrectPass1!")
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.user.email, "alice@example.com")
        self.assertEqual(out.user.first_name, "Alice")
        self.assertEqual(out.tokens.access, "fake-access-1")
        self.assertEqual(out.tokens.refresh, "fake-refresh-1")

    def test_fails_when_user_not_found(self) -> None:
        result = self.use_case.execute(
            LoginInput(email="ghost@example.com", password="CorrectPass1!")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "email")
        self.assertEqual(result.errors[0].code, "auth.email.invalid_credentials")
        self.assertEqual(result.errors[0].message, "Credenciales inválidas.")

    def test_fails_for_wrong_password(self) -> None:
        result = self.use_case.execute(
            LoginInput(email="alice@example.com", password="WrongPass1!")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "password")
        self.assertEqual(result.errors[0].code, "auth.password.invalid_credentials")
        self.assertEqual(result.errors[0].message, "Credenciales inválidas.")

    def test_fails_when_user_inactive(self) -> None:
        self.repo.seed(
            email="bob@example.com",
            password_hash=make_password("CorrectPass1!"),
            is_active=False,
        )
        result = self.use_case.execute(
            LoginInput(email="bob@example.com", password="CorrectPass1!")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "email")
        self.assertEqual(result.errors[0].code, "auth.email.inactive")
        self.assertEqual(result.errors[0].message, "La cuenta está inactiva.")

    def test_email_lookup_is_case_insensitive(self) -> None:
        result = self.use_case.execute(
            LoginInput(email="ALICE@EXAMPLE.COM", password="CorrectPass1!")
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.user.email, "alice@example.com")

    def test_fails_with_invalid_email_format(self) -> None:
        result = self.use_case.execute(
            LoginInput(email="not-an-email", password="CorrectPass1!")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "email")
        self.assertEqual(result.errors[0].code, "auth.email.invalid_format")
        self.assertEqual(
            result.errors[0].message, "Ingresa un correo electrónico válido."
        )

    def test_fails_when_password_missing(self) -> None:
        result = self.use_case.execute(
            LoginInput(email="alice@example.com", password="")
        )
        self.assertFalse(result.is_success)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, "password")
        self.assertEqual(result.errors[0].code, "auth.password.required")
        self.assertEqual(result.errors[0].message, "La contraseña es obligatoria.")

    def test_accumulates_invalid_format_and_required_errors(self) -> None:
        result = self.use_case.execute(LoginInput(email="not-an-email", password=""))
        self.assertFalse(result.is_success)
        fields = [e.field for e in result.errors]
        codes = [e.code for e in result.errors]
        self.assertIn("email", fields)
        self.assertIn("password", fields)
        self.assertIn("auth.email.invalid_format", codes)
        self.assertIn("auth.password.required", codes)
        self.assertEqual(len(result.errors), 2)

    def test_does_not_leak_existence_via_field_or_message(self) -> None:
        not_found = self.use_case.execute(
            LoginInput(email="ghost@example.com", password="Anything1!")
        )
        wrong_pw = self.use_case.execute(
            LoginInput(email="alice@example.com", password="WrongPass1!")
        )
        # Different fields so the client can show the error on the right input,
        # but the messages match so the attacker can't tell which emails exist.
        self.assertNotEqual(not_found.errors[0].field, wrong_pw.errors[0].field)
        self.assertNotEqual(not_found.errors[0].code, wrong_pw.errors[0].code)
        self.assertEqual(not_found.errors[0].message, wrong_pw.errors[0].message)