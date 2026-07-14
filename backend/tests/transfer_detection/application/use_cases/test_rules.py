"""Unit tests for transfer detection rule CRUD use cases."""

from __future__ import annotations

import unittest

from django.utils import translation

from modules.transfer_detection.application.dtos import (
    CreateTransferDetectionRuleInput,
    UpdateTransferDetectionRuleInput,
)
from modules.transfer_detection.application.use_cases.activate_rule import (
    ActivateTransferDetectionRuleUseCase,
)
from modules.transfer_detection.application.use_cases.create_rule import (
    CreateTransferDetectionRuleUseCase,
)
from modules.transfer_detection.application.use_cases.deactivate_rule import (
    DeactivateTransferDetectionRuleUseCase,
)
from modules.transfer_detection.application.use_cases.delete_rule import (
    DeleteTransferDetectionRuleUseCase,
)
from modules.transfer_detection.application.use_cases.get_rule import (
    GetTransferDetectionRuleUseCase,
)
from modules.transfer_detection.application.use_cases.list_rules import (
    ListTransferDetectionRulesUseCase,
)
from modules.transfer_detection.application.use_cases.update_rule import (
    UpdateTransferDetectionRuleUseCase,
)

from tests.fakes import InMemoryTransferDetectionRuleRepository


class TestCreateTransferDetectionRuleUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryTransferDetectionRuleRepository()
        self.use_case = CreateTransferDetectionRuleUseCase(repository=self.repo)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_creates_rule_with_valid_data(self) -> None:
        result = self.use_case.execute(
            CreateTransferDetectionRuleInput(
                owner_id=1, pattern="transferencia", match_type="contains", priority=5
            )
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.pattern, "transferencia")
        self.assertEqual(result.value.priority, 5)
        self.assertTrue(result.value.is_active)

    def test_rejects_invalid_match_type(self) -> None:
        result = self.use_case.execute(
            CreateTransferDetectionRuleInput(
                owner_id=1, pattern="x", match_type="regex", priority=0
            )
        )
        self.assertFalse(result.is_success)
        codes = [e.code for e in result.errors]
        self.assertIn("transfer_detection.match_type.invalid", codes)

    def test_rejects_duplicate_active_pattern(self) -> None:
        self.use_case.execute(
            CreateTransferDetectionRuleInput(
                owner_id=1, pattern="transferencia", match_type="contains", priority=0
            )
        )
        result = self.use_case.execute(
            CreateTransferDetectionRuleInput(
                owner_id=1, pattern="transferencia", match_type="contains", priority=0
            )
        )
        self.assertFalse(result.is_success)
        codes = [e.code for e in result.errors]
        self.assertIn("transfer_detection.pattern.already_exists", codes)


class TestUpdateTransferDetectionRuleUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryTransferDetectionRuleRepository()
        self.rule = self.repo.seed(
            owner_id=1, pattern="transf", match_type="contains", priority=0
        )
        self.use_case = UpdateTransferDetectionRuleUseCase(repository=self.repo)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_updates_priority(self) -> None:
        result = self.use_case.execute(
            1, self.rule.id, UpdateTransferDetectionRuleInput(priority=10)
        )
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.priority, 10)

    def test_inactive_rule_cannot_be_edited(self) -> None:
        self.repo.deactivate(self.rule.id)
        result = self.use_case.execute(
            1, self.rule.id, UpdateTransferDetectionRuleInput(priority=10)
        )
        self.assertFalse(result.is_success)
        codes = [e.code for e in result.errors]
        self.assertIn("transfer_detection.rule.inactive", codes)


class TestActivateDeactivateTransferDetectionRuleUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryTransferDetectionRuleRepository()
        self.rule = self.repo.seed(
            owner_id=1, pattern="transf", match_type="contains", priority=0
        )
        self.deactivate = DeactivateTransferDetectionRuleUseCase(repository=self.repo)
        self.activate = ActivateTransferDetectionRuleUseCase(repository=self.repo)

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_deactivate_then_activate(self) -> None:
        off = self.deactivate.execute(1, self.rule.id)
        self.assertTrue(off.is_success)
        self.assertFalse(off.value.is_active)
        on = self.activate.execute(1, self.rule.id)
        self.assertTrue(on.is_success)
        self.assertTrue(on.value.is_active)

    def test_already_active_returns_error(self) -> None:
        result = self.activate.execute(1, self.rule.id)
        self.assertFalse(result.is_success)
        codes = [e.code for e in result.errors]
        self.assertIn("transfer_detection.rule.already_active", codes)


class TestGetListDeleteTransferDetectionRuleUseCase(unittest.TestCase):
    def setUp(self) -> None:
        translation.activate("es")
        self.repo = InMemoryTransferDetectionRuleRepository()
        self.rule = self.repo.seed(
            owner_id=1, pattern="transf", match_type="contains", priority=0
        )

    def tearDown(self) -> None:
        translation.deactivate_all()

    def test_get_returns_rule(self) -> None:
        use_case = GetTransferDetectionRuleUseCase(repository=self.repo)
        result = use_case.execute(1, self.rule.id)
        self.assertTrue(result.is_success)
        self.assertEqual(result.value.pattern, "transf")

    def test_get_unknown_returns_not_found(self) -> None:
        use_case = GetTransferDetectionRuleUseCase(repository=self.repo)
        result = use_case.execute(1, 9999)
        self.assertFalse(result.is_success)
        codes = [e.code for e in result.errors]
        self.assertIn("transfer_detection.rule.not_found", codes)

    def test_list_returns_rules(self) -> None:
        use_case = ListTransferDetectionRulesUseCase(repository=self.repo)
        result = use_case.execute(1)
        self.assertTrue(result.is_success)
        self.assertEqual(len(result.value), 1)

    def test_delete_removes_rule(self) -> None:
        use_case = DeleteTransferDetectionRuleUseCase(repository=self.repo)
        result = use_case.execute(1, self.rule.id)
        self.assertTrue(result.is_success)
        self.assertIsNone(self.repo.find_by_id(self.rule.id))


if __name__ == "__main__":
    unittest.main()