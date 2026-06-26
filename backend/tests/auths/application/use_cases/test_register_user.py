"""Unit tests for RegisterUserUseCase."""

from __future__ import annotations

import unittest

from django.contrib.auth.hashers import check_password, identify_hasher

from modules.auths.application.dtos import RegisterInput
from modules.auths.application.use_cases.register_user import RegisterUserUseCase
from modules.auths.domain.exceptions import UserAlreadyExistsError
from modules.auths.domain.value_objects import InvalidEmailError

from tests.fakes import FakeTokenService, InMemoryUserRepository


class TestRegisterUserUseCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = InMemoryUserRepository()
        self.tokens = FakeTokenService()
        self.use_case = RegisterUserUseCase(repository=self.repo, token_service=self.tokens)

    def test_creates_user_and_returns_tokens(self) -> None:
        out = self.use_case.execute(
            RegisterInput(email="a@b.com", password="Strong123!", first_name="A", last_name="B")
        )

        self.assertTrue(self.repo.exists_by_email("a@b.com"))
        self.assertEqual(out.user.email, "a@b.com")
        self.assertEqual(out.user.first_name, "A")
        self.assertEqual(out.user.last_name, "B")
        self.assertTrue(out.user.is_active)
        self.assertEqual(out.tokens.access, "fake-access-1")
        self.assertEqual(out.tokens.refresh, "fake-refresh-1")

    def test_hashes_password(self) -> None:
        self.use_case.execute(RegisterInput(email="a@b.com", password="Strong123!"))

        password_hash = self.repo.get_password_hash("a@b.com")
        self.assertIsNotNone(password_hash)
        self.assertNotEqual(password_hash, "Strong123!")
        self.assertTrue(check_password("Strong123!", password_hash))
        # ensure it's a real Django hasher, not plain text
        self.assertEqual(identify_hasher(password_hash).algorithm, "pbkdf2_sha256")

    def test_raises_when_email_already_exists(self) -> None:
        self.use_case.execute(RegisterInput(email="dup@b.com", password="Strong123!"))

        with self.assertRaises(UserAlreadyExistsError):
            self.use_case.execute(RegisterInput(email="dup@b.com", password="OtherPass1!"))

    def test_email_match_is_case_insensitive_for_uniqueness(self) -> None:
        self.use_case.execute(RegisterInput(email="Foo@Bar.com", password="Strong123!"))

        with self.assertRaises(UserAlreadyExistsError):
            self.use_case.execute(RegisterInput(email="foo@bar.com", password="OtherPass1!"))

    def test_rejects_invalid_email(self) -> None:
        with self.assertRaises(InvalidEmailError):
            self.use_case.execute(RegisterInput(email="not-an-email", password="Strong123!"))

    def test_token_service_is_invoked_with_new_user_id(self) -> None:
        out = self.use_case.execute(RegisterInput(email="a@b.com", password="Strong123!"))

        self.assertEqual(self.tokens.generated, [out.user.id])
