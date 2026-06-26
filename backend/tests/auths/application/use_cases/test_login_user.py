"""Unit tests for LoginUserUseCase."""

from __future__ import annotations

import unittest

from django.contrib.auth.hashers import make_password

from modules.auths.application.dtos import LoginInput
from modules.auths.application.use_cases.login_user import LoginUserUseCase
from modules.auths.domain.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from modules.auths.domain.value_objects import InvalidEmailError

from tests.fakes import FakeTokenService, InMemoryUserRepository


class TestLoginUserUseCase(unittest.TestCase):
    def setUp(self) -> None:
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

    def test_returns_tokens_for_valid_credentials(self) -> None:
        out = self.use_case.execute(
            LoginInput(email="alice@example.com", password="CorrectPass1!")
        )

        self.assertEqual(out.user.email, "alice@example.com")
        self.assertEqual(out.user.first_name, "Alice")
        self.assertEqual(out.tokens.access, "fake-access-1")
        self.assertEqual(out.tokens.refresh, "fake-refresh-1")

    def test_raises_user_not_found(self) -> None:
        with self.assertRaises(UserNotFoundError):
            self.use_case.execute(
                LoginInput(email="ghost@example.com", password="CorrectPass1!")
            )

    def test_raises_invalid_credentials_for_wrong_password(self) -> None:
        with self.assertRaises(InvalidCredentialsError):
            self.use_case.execute(
                LoginInput(email="alice@example.com", password="WrongPass1!")
            )

    def test_raises_inactive_when_user_disabled(self) -> None:
        self.repo.seed(
            email="bob@example.com",
            password_hash=make_password("CorrectPass1!"),
            is_active=False,
        )

        with self.assertRaises(InactiveUserError):
            self.use_case.execute(
                LoginInput(email="bob@example.com", password="CorrectPass1!")
            )

    def test_email_lookup_is_case_insensitive(self) -> None:
        out = self.use_case.execute(
            LoginInput(email="ALICE@EXAMPLE.COM", password="CorrectPass1!")
        )
        self.assertEqual(out.user.email, "alice@example.com")

    def test_rejects_invalid_email_format(self) -> None:
        with self.assertRaises(InvalidEmailError):
            self.use_case.execute(
                LoginInput(email="not-an-email", password="CorrectPass1!")
            )
