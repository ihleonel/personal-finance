"""Unit tests for categorization rule CRUD use cases using in-memory fakes."""

from __future__ import annotations

import unittest

from django.utils import translation

from modules.categorization_rules.application.dtos import (
    CreateCategorizationRuleInput,
    UpdateCategorizationRuleInput,
)
from modules.categorization_rules.application.use_cases.activate_rule import (
    ActivateCategorizationRuleUseCase,
)
from modules.categorization_rules.application.use_cases.create_rule import (
    CreateCategorizationRuleUseCase,
)
from modules.categorization_rules.application.use_cases.deactivate_rule import (
    DeactivateCategorizationRuleUseCase,
)
from modules.categorization_rules.application.use_cases.delete_rule import (
    DeleteCategorizationRuleUseCase,
)
from modules.categorization_rules.application.use_cases.get_rule import (
    GetCategorizationRuleUseCase,
)
from modules.categorization_rules.application.use_cases.list_rules import (
    ListCategorizationRulesUseCase,
)
from modules.categorization_rules.application.use_cases.update_rule import (
    UpdateCategorizationRuleUseCase,
)
from tests.fakes import (
    InMemoryCategoryRepository,
    InMemoryCategorizationRuleRepository,
)


class TestCreateCategorizationRuleUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.rule_repo = InMemoryCategorizationRuleRepository()
        self.category_repo = InMemoryCategoryRepository()
        self.category = self.category_repo.seed(owner_id=1, name="Comida")
        self.use_case = CreateCategorizationRuleUseCase(repository=self.rule_repo)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_creates_rule_with_valid_data(self) -> None:
        result = self.use_case.execute(
            CreateCategorizationRuleInput(
                owner_id=1,
                pattern="coto",
                match_type="contains",
                category_id=self.category.id,
                kind="expense",
                priority=5,
            )
        )
        self.assertTrue(result.is_success)
        out = result.value
        self.assertEqual(out.pattern, "coto")
        self.assertEqual(out.match_type, "contains")
        self.assertEqual(out.category_id, self.category.id)
        self.assertEqual(out.kind, "expense")
        self.assertEqual(out.priority, 5)
        self.assertTrue(out.is_active)

    def test_empty_pattern_fails(self) -> None:
        result = self.use_case.execute(
            CreateCategorizationRuleInput(
                owner_id=1,
                pattern="  ",
                match_type="contains",
                category_id=self.category.id,
                kind="expense",
                priority=0,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "pattern")
        self.assertEqual(result.errors[0].code, "categorization_rules.pattern.required")

    def test_invalid_match_type_fails(self) -> None:
        result = self.use_case.execute(
            CreateCategorizationRuleInput(
                owner_id=1,
                pattern="coto",
                match_type="regex",
                category_id=self.category.id,
                kind="expense",
                priority=0,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "match_type")

    def test_invalid_kind_fails(self) -> None:
        result = self.use_case.execute(
            CreateCategorizationRuleInput(
                owner_id=1,
                pattern="coto",
                match_type="contains",
                category_id=self.category.id,
                kind="other",
                priority=0,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "kind")

    def test_invalid_category_id_fails(self) -> None:
        result = self.use_case.execute(
            CreateCategorizationRuleInput(
                owner_id=1,
                pattern="coto",
                match_type="contains",
                category_id=0,
                kind="expense",
                priority=0,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "category_id")

    def test_negative_priority_fails(self) -> None:
        result = self.use_case.execute(
            CreateCategorizationRuleInput(
                owner_id=1,
                pattern="coto",
                match_type="contains",
                category_id=self.category.id,
                kind="expense",
                priority=-1,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "priority")

    def test_duplicate_active_pattern_fails(self) -> None:
        self.use_case.execute(
            CreateCategorizationRuleInput(
                owner_id=1,
                pattern="coto",
                match_type="contains",
                category_id=self.category.id,
                kind="expense",
                priority=0,
            )
        )
        result = self.use_case.execute(
            CreateCategorizationRuleInput(
                owner_id=1,
                pattern="coto",
                match_type="contains",
                category_id=self.category.id,
                kind="expense",
                priority=0,
            )
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categorization_rules.pattern.already_exists")

    def test_same_pattern_different_match_type_allowed(self) -> None:
        first = self.use_case.execute(
            CreateCategorizationRuleInput(
                owner_id=1,
                pattern="coto",
                match_type="contains",
                category_id=self.category.id,
                kind="expense",
                priority=0,
            )
        )
        self.assertTrue(first.is_success)
        second = self.use_case.execute(
            CreateCategorizationRuleInput(
                owner_id=1,
                pattern="coto",
                match_type="equals",
                category_id=self.category.id,
                kind="expense",
                priority=0,
            )
        )
        self.assertTrue(second.is_success)


class TestListGetCategorizationRulesUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.rule_repo = InMemoryCategorizationRuleRepository()
        self.category_repo = InMemoryCategoryRepository()
        self.category = self.category_repo.seed(owner_id=1, name="Comida")
        self.r1 = self.rule_repo.seed(
            owner_id=1, pattern="coto", match_type="contains",
            category_id=self.category.id, priority=1,
        )
        self.r2 = self.rule_repo.seed(
            owner_id=1, pattern="uber", match_type="contains",
            category_id=self.category.id, priority=10,
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_list_returns_owner_rules_ordered_by_priority(self) -> None:
        result = ListCategorizationRulesUseCase(repository=self.rule_repo).execute(1)
        self.assertTrue(result.is_success)
        ids = [r.id for r in result.value]
        self.assertEqual(ids, [self.r2.id, self.r1.id])

    def test_list_excludes_other_owners(self) -> None:
        self.rule_repo.seed(
            owner_id=2, pattern="x", match_type="contains",
            category_id=self.category.id,
        )
        result = ListCategorizationRulesUseCase(repository=self.rule_repo).execute(1)
        self.assertEqual(len(result.value), 2)

    def test_get_returns_rule(self) -> None:
        result = GetCategorizationRuleUseCase(repository=self.rule_repo).execute(1, self.r1.id)
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.pattern, "coto")

    def test_get_other_owner_not_found(self) -> None:
        result = GetCategorizationRuleUseCase(repository=self.rule_repo).execute(2, self.r1.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categorization_rules.rule.not_found")

    def test_get_missing_not_found(self) -> None:
        result = GetCategorizationRuleUseCase(repository=self.rule_repo).execute(1, 9999)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categorization_rules.rule.not_found")


class TestUpdateCategorizationRuleUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.rule_repo = InMemoryCategorizationRuleRepository()
        self.category_repo = InMemoryCategoryRepository()
        self.category = self.category_repo.seed(owner_id=1, name="Comida")
        self.other = self.category_repo.seed(owner_id=1, name="Transporte")
        self.rule = self.rule_repo.seed(
            owner_id=1, pattern="coto", match_type="contains",
            category_id=self.category.id,
        )
        self.use_case = UpdateCategorizationRuleUseCase(repository=self.rule_repo)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_update_pattern_and_category(self) -> None:
        result = self.use_case.execute(
            1,
            self.rule.id,
            UpdateCategorizationRuleInput(pattern="carrefour", category_id=self.other.id),
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.pattern, "carrefour")
        self.assertEqual(result.value.category_id, self.other.id)

    def test_empty_payload_fails(self) -> None:
        result = self.use_case.execute(1, self.rule.id, UpdateCategorizationRuleInput())
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categorization_rules.rule.empty_payload")

    def test_invalid_match_type_fails(self) -> None:
        result = self.use_case.execute(
            1, self.rule.id, UpdateCategorizationRuleInput(match_type="regex"),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].field, "match_type")

    def test_update_to_duplicate_pattern_fails(self) -> None:
        self.rule_repo.seed(
            owner_id=1, pattern="uber", match_type="contains",
            category_id=self.category.id,
        )
        result = self.use_case.execute(
            1, self.rule.id, UpdateCategorizationRuleInput(pattern="uber"),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categorization_rules.pattern.already_exists")

    def test_update_inactive_rule_fails(self) -> None:
        self.rule_repo.deactivate(self.rule.id)
        result = self.use_case.execute(
            1, self.rule.id, UpdateCategorizationRuleInput(pattern="x"),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categorization_rules.rule.inactive")

    def test_update_other_owner_not_found(self) -> None:
        result = self.use_case.execute(
            2, self.rule.id, UpdateCategorizationRuleInput(pattern="x"),
        )
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categorization_rules.rule.not_found")


class TestActivateDeactivateCategorizationRuleUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.rule_repo = InMemoryCategorizationRuleRepository()
        self.category_repo = InMemoryCategoryRepository()
        self.category = self.category_repo.seed(owner_id=1, name="Comida")
        self.rule = self.rule_repo.seed(
            owner_id=1, pattern="coto", match_type="contains",
            category_id=self.category.id,
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_deactivate_marks_inactive(self) -> None:
        result = DeactivateCategorizationRuleUseCase(repository=self.rule_repo).execute(1, self.rule.id)
        self.assertTrue(result.is_success)
        self.assertFalse(result.value.is_active)

    def test_deactivate_already_inactive_fails(self) -> None:
        self.rule_repo.deactivate(self.rule.id)
        result = DeactivateCategorizationRuleUseCase(repository=self.rule_repo).execute(1, self.rule.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categorization_rules.rule.already_inactive")

    def test_activate_marks_active(self) -> None:
        self.rule_repo.deactivate(self.rule.id)
        result = ActivateCategorizationRuleUseCase(repository=self.rule_repo).execute(1, self.rule.id)
        self.assertTrue(result.is_success)
        self.assertTrue(result.value.is_active)

    def test_activate_already_active_fails(self) -> None:
        result = ActivateCategorizationRuleUseCase(repository=self.rule_repo).execute(1, self.rule.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categorization_rules.rule.already_active")

    def test_activate_conflict_fails(self) -> None:
        self.rule_repo.deactivate(self.rule.id)
        self.rule_repo.seed(
            owner_id=1, pattern="coto", match_type="contains",
            category_id=self.category.id,
        )
        result = ActivateCategorizationRuleUseCase(repository=self.rule_repo).execute(1, self.rule.id)
        self.assertFalse(result.is_success)
        self.assertEqual(result.errors[0].code, "categorization_rules.pattern.already_exists")


class TestDeleteCategorizationRuleUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.rule_repo = InMemoryCategorizationRuleRepository()
        self.category_repo = InMemoryCategoryRepository()
        self.category = self.category_repo.seed(owner_id=1, name="Comida")
        self.rule = self.rule_repo.seed(
            owner_id=1, pattern="coto", match_type="contains",
            category_id=self.category.id,
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_delete_removes_rule(self) -> None:
        result = DeleteCategorizationRuleUseCase(repository=self.rule_repo).execute(1, self.rule.id)
        self.assertTrue(result.is_success)
        self.assertIsNone(self.rule_repo.find_by_id(self.rule.id))

    def test_delete_other_owner_not_found(self) -> None:
        result = DeleteCategorizationRuleUseCase(repository=self.rule_repo).execute(2, self.rule.id)
        self.assertFalse(result.is_success)
        self.assertIsNotNone(self.rule_repo.find_by_id(self.rule.id))


if __name__ == "__main__":
    unittest.main()