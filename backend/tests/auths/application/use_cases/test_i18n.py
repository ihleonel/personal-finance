"""i18n sanity tests.

Verifies:
- Spanish is the active language by default (settings.LANGUAGE_CODE).
- Use case messages render in Spanish when es is active.
- The stable error `code` does NOT change with the language.
"""

from __future__ import annotations

import unittest

from django.conf import settings
from django.utils import translation

from modules.auths.application.dtos import RegisterInput
from modules.auths.application.use_cases.register_user import RegisterUserUseCase

from tests.fakes import FakeTokenService, InMemoryUserRepository


class TestI18nDefaults(unittest.TestCase):
    def test_default_language_is_spanish(self) -> None:
        self.assertEqual(settings.LANGUAGE_CODE, "es")

    def test_spanish_in_available_languages(self) -> None:
        codes = [code for code, _ in settings.LANGUAGES]
        self.assertIn("es", codes)


class TestUseCaseMessagesInSpanish(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.use_case = RegisterUserUseCase(
            repository=InMemoryUserRepository(),
            token_service=FakeTokenService(),
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_invalid_email_message_is_in_spanish(self) -> None:
        result = self.use_case.execute(
            RegisterInput(email="not-an-email", password="Strong123!")
        )
        self.assertFalse(result.is_success)
        err = result.errors[0]
        self.assertEqual(err.code, "auth.email.invalid_format")
        self.assertEqual(err.message, "Ingresa un correo electrónico válido.")

    def test_code_is_stable_across_languages(self) -> None:
        # Even if we activate a non-installed language, the code stays stable.
        translation.activate("fr")
        try:
            result = self.use_case.execute(
                RegisterInput(email="not-an-email", password="Strong123!")
            )
            self.assertFalse(result.is_success)
            self.assertEqual(result.errors[0].code, "auth.email.invalid_format")
        finally:
            translation.activate("es")