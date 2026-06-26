"""Unit tests for GetUserProfileUseCase."""

from __future__ import annotations

import unittest

from modules.auths.application.use_cases.get_user_profile import GetUserProfileUseCase
from modules.auths.domain.exceptions import UserNotFoundError

from tests.fakes import InMemoryUserRepository


class TestGetUserProfileUseCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = InMemoryUserRepository()
        self.use_case = GetUserProfileUseCase(repository=self.repo)
        self.user = self.repo.seed(
            email="alice@example.com",
            password_hash="hash",
            first_name="Alice",
            last_name="Liddell",
            is_active=True,
        )

    def test_returns_profile_for_existing_user(self) -> None:
        out = self.use_case.execute(self.user.id)

        self.assertEqual(out.id, self.user.id)
        self.assertEqual(out.email, "alice@example.com")
        self.assertEqual(out.first_name, "Alice")
        self.assertEqual(out.last_name, "Liddell")
        self.assertTrue(out.is_active)

    def test_raises_user_not_found(self) -> None:
        with self.assertRaises(UserNotFoundError):
            self.use_case.execute(99999)

    def test_reflects_inactive_status(self) -> None:
        self.repo.seed(
            email="bob@example.com",
            password_hash="hash",
            first_name="Bob",
            last_name="Dylan",
            is_active=False,
        )

        out = self.use_case.execute(self.repo.find_by_email("bob@example.com").id)
        self.assertFalse(out.is_active)