"""Unit tests for SuggestCategoryUseCase using in-memory fakes."""

from __future__ import annotations

import unittest

from django.utils import translation

from modules.categorization_rules.application.categorizer import (
    CategorySuggestionService,
)
from modules.categorization_rules.application.dtos import SuggestCategoryInput
from modules.categorization_rules.application.use_cases.suggest_category import (
    SuggestCategoryUseCase,
)
from tests.fakes import (
    FakeCategoryNameResolver,
    InMemoryCategorizationRuleRepository,
    InMemoryCategoryRepository,
)


class TestSuggestCategoryUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.category_repo = InMemoryCategoryRepository()
        self.rule_repo = InMemoryCategorizationRuleRepository()
        self.comida = self.category_repo.seed(owner_id=1, name="Comida", kind="expense")
        self.transporte = self.category_repo.seed(owner_id=1, name="Transporte", kind="expense")
        # Regla alta prioridad para uber
        self.rule_repo.seed(
            owner_id=1, pattern="uber", match_type="contains",
            category_id=self.transporte.id, priority=10,
        )
        # Regla más baja para coto
        self.rule_repo.seed(
            owner_id=1, pattern="coto", match_type="contains",
            category_id=self.comida.id, priority=1,
        )
        self.use_case = SuggestCategoryUseCase(
            rule_repository=self.rule_repo,
            name_resolver=FakeCategoryNameResolver(self.category_repo),
            suggestion_service=CategorySuggestionService(),
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_suggest_returns_category_id_and_name(self) -> None:
        result = self.use_case.execute(
            SuggestCategoryInput(owner_id=1, description="PAGO UBER TRIP 1234")
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.category_id, self.transporte.id)
        self.assertEqual(result.value.category_name, "Transporte")

    def test_suggest_normalizes_accents(self) -> None:
        result = self.use_case.execute(
            SuggestCategoryInput(owner_id=1, description="COMPRA COTÓ")
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.category_id, self.comida.id)

    def test_no_match_returns_none(self) -> None:
        result = self.use_case.execute(
            SuggestCategoryInput(owner_id=1, description="algo desconocido")
        )
        self.assertTrue(result.is_success)
        self.assertIsNone(result.value.category_id)
        self.assertIsNone(result.value.category_name)

    def test_empty_description_returns_none(self) -> None:
        result = self.use_case.execute(SuggestCategoryInput(owner_id=1, description=""))
        self.assertTrue(result.is_success)
        self.assertIsNone(result.value.category_id)

    def test_only_active_rules_are_used(self) -> None:
        # Desactivamos la regla de uber
        uber_rule = next(
            r for r in self.rule_repo.list_by_owner(1) if r.pattern == "uber"
        )
        self.rule_repo.deactivate(uber_rule.id)
        result = self.use_case.execute(
            SuggestCategoryInput(owner_id=1, description="PAGO UBER")
        )
        self.assertTrue(result.is_success)
        self.assertIsNone(result.value.category_id)

    def test_priority_order_higher_first(self) -> None:
        # Regla genérica de menor prioridad que también matchea
        self.rule_repo.seed(
            owner_id=1, pattern="pago", match_type="contains",
            category_id=self.comida.id, priority=0,
        )
        result = self.use_case.execute(
            SuggestCategoryInput(owner_id=1, description="PAGO UBER")
        )
        self.assertEqual(result.value.category_id, self.transporte.id)

    def test_other_owner_rules_not_used(self) -> None:
        result = self.use_case.execute(
            SuggestCategoryInput(owner_id=2, description="PAGO UBER")
        )
        self.assertTrue(result.is_success)
        self.assertIsNone(result.value.category_id)


if __name__ == "__main__":
    unittest.main()