"""Unit tests for CategorySuggestionService (pure matching/normalization)."""

from __future__ import annotations

import unittest
from dataclasses import dataclass

from modules.categorization_rules.application.categorizer import (
    CategorySuggestionService,
)
from modules.categorization_rules.domain.entities import CategorizationRule
from modules.categorization_rules.domain.value_objects import normalize_description


@dataclass
class _FakeRule:
    pattern: str
    match_type: str
    category_id: int
    is_active: bool = True


class TestNormalizeDescription(unittest.TestCase):
    def test_lowercases(self) -> None:
        self.assertEqual(normalize_description("MERCADOPAGO"), "mercadopago")

    def test_strips_diacritics(self) -> None:
        self.assertEqual(normalize_description("CAFÉ NÚÑEZ"), "cafe nunez")

    def test_removes_digits(self) -> None:
        self.assertEqual(
            normalize_description("PAGO 1234 COTO"),
            "pago coto",
        )

    def test_collapses_spaces(self) -> None:
        self.assertEqual(
            normalize_description("   varios    espacios   "),
            "varios espacios",
        )

    def test_empty_returns_empty(self) -> None:
        self.assertEqual(normalize_description(""), "")
        self.assertEqual(normalize_description(None), "")  # type: ignore[arg-type]


class TestCategorySuggestionService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = CategorySuggestionService()

    def test_contains_match_returns_category(self) -> None:
        rules = [_FakeRule("coto", "contains", 5)]
        self.assertEqual(self.service.suggest("PAGO COTO 1234", rules), 5)

    def test_equals_match_only_exact(self) -> None:
        rules = [_FakeRule("cafe", "equals", 7)]
        self.assertIsNone(self.service.suggest("cafe nunez", rules))
        self.assertEqual(self.service.suggest("CAFE", rules), 7)

    def test_no_match_returns_none(self) -> None:
        rules = [_FakeRule("uber", "contains", 3)]
        self.assertIsNone(self.service.suggest("PAGO COTO", rules))

    def test_priority_higher_first(self) -> None:
        rules = [
            _FakeRule("coto", "contains", 1, is_active=True),
            _FakeRule("coto", "contains", 2, is_active=True),
        ]
        # Las reglas ya vienen ordenadas por prioridad desc; el service respeta el orden.
        self.assertEqual(self.service.suggest("COTO", rules), 1)

    def test_inactive_rules_are_ignored(self) -> None:
        rules = [_FakeRule("coto", "contains", 5, is_active=False)]
        self.assertIsNone(self.service.suggest("COTO", rules))

    def test_normalization_accent_insensitive(self) -> None:
        rules = [_FakeRule("cafe", "contains", 9)]
        self.assertEqual(self.service.suggest("COMPRA CAFÉ NÚÑEZ", rules), 9)

    def test_empty_pattern_rule_is_ignored(self) -> None:
        rules = [_FakeRule("   ", "contains", 11)]
        self.assertIsNone(self.service.suggest("cualquier cosa", rules))

    def test_empty_description_returns_none(self) -> None:
        self.assertIsNone(self.service.suggest("", []))
        self.assertIsNone(self.service.suggest("   ", [_FakeRule("x", "contains", 1)]))


if __name__ == "__main__":
    unittest.main()