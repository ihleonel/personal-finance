"""Unit tests for GetCurrentUserUseCase."""

from __future__ import annotations

import unittest

from modules.auths.application.use_cases.get_current_user import GetCurrentUserUseCase
from modules.auths.domain.entities import User


class TestGetCurrentUserUseCase(unittest.TestCase):
    def setUp(self) -> None:
        self.use_case = GetCurrentUserUseCase()

    def test_maps_entity_to_output(self) -> None:
        user = User(
            id=42,
            email="me@example.com",
            first_name="Me",
            last_name="Now",
            is_active=True,
        )

        out = self.use_case.execute(user)

        self.assertEqual(out.id, 42)
        self.assertEqual(out.email, "me@example.com")
        self.assertEqual(out.first_name, "Me")
        self.assertEqual(out.last_name, "Now")
        self.assertTrue(out.is_active)

    def test_inactive_user_is_reflected_in_output(self) -> None:
        user = User(
            id=7,
            email="x@y.com",
            first_name="",
            last_name="",
            is_active=False,
        )

        out = self.use_case.execute(user)

        self.assertFalse(out.is_active)
