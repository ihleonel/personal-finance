from __future__ import annotations

from dataclasses import dataclass

from modules.categorization_rules.application.categorizer import (
    CategorySuggestionService,
)
from modules.categorization_rules.application.dtos import (
    SuggestCategoryInput,
    SuggestCategoryOutput,
)
from modules.categorization_rules.application.ports import CategoryNameResolver
from modules.categorization_rules.domain.repositories import (
    CategorizationRuleRepository,
)
from modules.shared.application.result import Result


@dataclass
class SuggestCategoryUseCase:
    rule_repository: CategorizationRuleRepository
    name_resolver: CategoryNameResolver
    suggestion_service: CategorySuggestionService

    def execute(self, data: SuggestCategoryInput) -> Result[SuggestCategoryOutput]:
        rules = self.rule_repository.list_active_by_owner(data.owner_id)
        category_id = self.suggestion_service.suggest(data.description, rules)
        if category_id is None:
            return Result.ok(SuggestCategoryOutput(category_id=None, category_name=None))

        name = self.name_resolver.find_name_by_id_and_owner(data.owner_id, category_id)
        return Result.ok(SuggestCategoryOutput(category_id=category_id, category_name=name))