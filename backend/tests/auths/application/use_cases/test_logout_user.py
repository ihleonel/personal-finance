"""Unit tests for LogoutUserUseCase."""

from __future__ import annotations

import unittest

from modules.auths.application.dtos import LogoutInput
from modules.auths.application.use_cases.logout_user import LogoutUserUseCase

from tests.fakes import FakeTokenService


class TestLogoutUserUseCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tokens = FakeTokenService()
        self.use_case = LogoutUserUseCase(token_service=self.tokens)

    def test_blacklists_refresh_token(self) -> None:
        refresh = "some-refresh-token"

        self.use_case.execute(LogoutInput(refresh=refresh))

        self.assertEqual(self.tokens.blacklisted, [refresh])

    def test_blacklists_multiple_refresh_tokens_in_order(self) -> None:
        self.use_case.execute(LogoutInput(refresh="t1"))
        self.use_case.execute(LogoutInput(refresh="t2"))

        self.assertEqual(self.tokens.blacklisted, ["t1", "t2"])
