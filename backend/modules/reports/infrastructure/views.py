from __future__ import annotations

from dataclasses import asdict

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.shared.application.result import ValidationError
from modules.reports.application.dtos import (
    CategorySummaryInput,
    IncomeExpenseSummaryInput,
)
from modules.reports.application.use_cases.get_income_expense_summary import (
    GetIncomeExpenseSummaryUseCase,
)
from modules.reports.application.use_cases.get_category_summary import (
    GetCategorySummaryUseCase,
)
from modules.categories.infrastructure.repositories import DjangoCategoryRepository
from modules.accounts.infrastructure.repositories import DjangoAccountRepository
from modules.transactions.infrastructure.repositories import DjangoTransactionRepository

from .serializers import (
    CategorySummaryQuerySerializer,
    IncomeExpenseSummaryQuerySerializer,
)


def _errors_to_drf(errors: list[ValidationError]) -> dict:
    out: dict[str, list[str]] = {}
    for e in errors:
        out.setdefault(e.field, []).append(e.message)
    return out


class IncomeExpenseSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        serializer = IncomeExpenseSummaryQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = GetIncomeExpenseSummaryUseCase(
            repository=DjangoTransactionRepository(),
            account_repository=DjangoAccountRepository(),
            category_repository=DjangoCategoryRepository(),
        )
        result = use_case.execute(
            IncomeExpenseSummaryInput(
                owner_id=request.user.id, **serializer.to_dto()
            )
        )

        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(asdict(result.value), status=status.HTTP_200_OK)


class CategorySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        serializer = CategorySummaryQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = GetCategorySummaryUseCase(
            repository=DjangoTransactionRepository(),
            category_repository=DjangoCategoryRepository(),
            account_repository=DjangoAccountRepository(),
        )
        result = use_case.execute(
            CategorySummaryInput(
                owner_id=request.user.id, **serializer.to_dto()
            )
        )

        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(asdict(result.value), status=status.HTTP_200_OK)