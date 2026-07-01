from __future__ import annotations

from dataclasses import asdict

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.categories.infrastructure.repositories import DjangoCategoryRepository
from modules.categorization_rules.application.categorizer import (
    CategorySuggestionService,
)
from modules.categorization_rules.application.dtos import (
    CreateCategorizationRuleInput,
    SuggestCategoryInput,
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
from modules.categorization_rules.application.use_cases.suggest_category import (
    SuggestCategoryUseCase,
)
from modules.categorization_rules.application.use_cases.update_rule import (
    UpdateCategorizationRuleUseCase,
)
from modules.categorization_rules.application.ports import CategoryNameResolver
from modules.categorization_rules.infrastructure.name_resolver import (
    CategoryRepositoryNameResolver,
)
from modules.categorization_rules.infrastructure.repositories import (
    DjangoCategorizationRuleRepository,
)
from modules.categorization_rules.infrastructure.serializers import (
    CreateCategorizationRuleSerializer,
    SuggestCategorySerializer,
    UpdateCategorizationRuleSerializer,
)
from modules.shared.application.result import ValidationError


def _repository() -> DjangoCategorizationRuleRepository:
    return DjangoCategorizationRuleRepository()


def _name_resolver() -> CategoryNameResolver:
    return CategoryRepositoryNameResolver(DjangoCategoryRepository())


def _suggestion_service() -> CategorySuggestionService:
    return CategorySuggestionService()


def _errors_to_drf(errors: list[ValidationError]) -> dict:
    out: dict[str, list[str]] = {}
    for e in errors:
        out.setdefault(e.field, []).append(e.message)
    return out


def _output_to_dict(output) -> dict:
    return asdict(output)


def _not_found_response(result) -> Response:
    code = result.errors[0].code if result.errors else ""
    if code == "categorization_rules.rule.not_found":
        return Response(
            {"detail": result.errors[0].message, "code": code},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(_errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST)


class CategorizationRuleListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        use_case = ListCategorizationRulesUseCase(repository=_repository())
        result = use_case.execute(request.user.id)
        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            [_output_to_dict(o) for o in result.value], status=status.HTTP_200_OK
        )

    def post(self, request: Request) -> Response:
        serializer = CreateCategorizationRuleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = CreateCategorizationRuleUseCase(repository=_repository())
        result = use_case.execute(
            CreateCategorizationRuleInput(
                owner_id=request.user.id, **serializer.to_dto()
            )
        )

        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            _output_to_dict(result.value), status=status.HTTP_201_CREATED
        )


class CategorizationRuleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, rule_id: int) -> Response:
        use_case = GetCategorizationRuleUseCase(repository=_repository())
        result = use_case.execute(request.user.id, rule_id)
        if not result.is_success:
            return _not_found_response(result)
        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)

    def patch(self, request: Request, rule_id: int) -> Response:
        serializer = UpdateCategorizationRuleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = UpdateCategorizationRuleUseCase(repository=_repository())
        result = use_case.execute(
            request.user.id,
            rule_id,
            UpdateCategorizationRuleInput(**serializer.to_dto()),
        )

        if not result.is_success:
            return _not_found_response(result)

        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)

    def delete(self, request: Request, rule_id: int) -> Response:
        use_case = DeleteCategorizationRuleUseCase(repository=_repository())
        result = use_case.execute(request.user.id, rule_id)
        if not result.is_success:
            return _not_found_response(result)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategorizationRuleDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, rule_id: int) -> Response:
        use_case = DeactivateCategorizationRuleUseCase(repository=_repository())
        result = use_case.execute(request.user.id, rule_id)
        if not result.is_success:
            return _not_found_response(result)
        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)


class CategorizationRuleActivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, rule_id: int) -> Response:
        use_case = ActivateCategorizationRuleUseCase(repository=_repository())
        result = use_case.execute(request.user.id, rule_id)
        if not result.is_success:
            return _not_found_response(result)
        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)


class SuggestCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = SuggestCategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = SuggestCategoryUseCase(
            rule_repository=_repository(),
            name_resolver=_name_resolver(),
            suggestion_service=_suggestion_service(),
        )
        result = use_case.execute(
            SuggestCategoryInput(
                owner_id=request.user.id, **serializer.to_dto()
            )
        )

        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)