from __future__ import annotations

from dataclasses import asdict

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.categories.application.dtos import CreateCategoryInput, UpdateCategoryInput
from modules.categories.application.use_cases.activate_category import ActivateCategoryUseCase
from modules.categories.application.use_cases.create_category import CreateCategoryUseCase
from modules.categories.application.use_cases.deactivate_category import DeactivateCategoryUseCase
from modules.categories.application.use_cases.get_category import GetCategoryUseCase
from modules.categories.application.use_cases.list_categories import ListCategoriesUseCase
from modules.categories.application.use_cases.update_category import UpdateCategoryUseCase
from modules.shared.application.result import ValidationError

from .repositories import DjangoCategoryRepository
from .serializers import CreateCategorySerializer, UpdateCategorySerializer


def _repository() -> DjangoCategoryRepository:
    return DjangoCategoryRepository()


def _errors_to_drf(errors: list[ValidationError]) -> dict:
    out: dict[str, list[str]] = {}
    for e in errors:
        out.setdefault(e.field, []).append(e.message)
    return out


def _output_to_dict(output) -> dict:
    return asdict(output)


class CategoryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        use_case = ListCategoriesUseCase(repository=_repository())
        result = use_case.execute(request.user.id)
        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            [_output_to_dict(o) for o in result.value], status=status.HTTP_200_OK
        )

    def post(self, request: Request) -> Response:
        serializer = CreateCategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = CreateCategoryUseCase(repository=_repository())
        result = use_case.execute(
            CreateCategoryInput(owner_id=request.user.id, **serializer.to_dto())
        )

        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            _output_to_dict(result.value), status=status.HTTP_201_CREATED
        )


class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, category_id: int) -> Response:
        use_case = GetCategoryUseCase(repository=_repository())
        result = use_case.execute(request.user.id, category_id)
        if not result.is_success:
            code = result.errors[0].code if result.errors else ""
            if code == "categories.category.not_found":
                return Response(
                    {"detail": result.errors[0].message, "code": code},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )
        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)

    def patch(self, request: Request, category_id: int) -> Response:
        serializer = UpdateCategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = UpdateCategoryUseCase(repository=_repository())
        result = use_case.execute(
            request.user.id, category_id, UpdateCategoryInput(**serializer.to_dto())
        )

        if not result.is_success:
            code = result.errors[0].code if result.errors else ""
            if code == "categories.category.not_found":
                return Response(
                    {"detail": result.errors[0].message, "code": code},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)


class CategoryDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, category_id: int) -> Response:
        use_case = DeactivateCategoryUseCase(repository=_repository())
        result = use_case.execute(request.user.id, category_id)
        if not result.is_success:
            code = result.errors[0].code if result.errors else ""
            if code == "categories.category.not_found":
                return Response(
                    {"detail": result.errors[0].message, "code": code},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )
        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)


class CategoryActivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, category_id: int) -> Response:
        use_case = ActivateCategoryUseCase(repository=_repository())
        result = use_case.execute(request.user.id, category_id)
        if not result.is_success:
            code = result.errors[0].code if result.errors else ""
            if code == "categories.category.not_found":
                return Response(
                    {"detail": result.errors[0].message, "code": code},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )
        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)