from __future__ import annotations

from dataclasses import asdict

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.accounts.application.dtos import CreateAccountInput, UpdateAccountInput
from modules.accounts.application.use_cases.create_account import CreateAccountUseCase
from modules.accounts.application.use_cases.deactivate_account import DeactivateAccountUseCase
from modules.accounts.application.use_cases.get_account import GetAccountUseCase
from modules.accounts.application.use_cases.list_accounts import ListAccountsUseCase
from modules.accounts.application.use_cases.update_account import UpdateAccountUseCase
from modules.shared.application.result import ValidationError

from .repositories import DjangoAccountRepository
from .serializers import CreateAccountSerializer, UpdateAccountSerializer


def _repository() -> DjangoAccountRepository:
    return DjangoAccountRepository()


def _errors_to_drf(errors: list[ValidationError]) -> dict:
    out: dict[str, list[str]] = {}
    for e in errors:
        out.setdefault(e.field, []).append(e.message)
    return out


def _output_to_dict(output) -> dict:
    return asdict(output)


class AccountListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        use_case = ListAccountsUseCase(repository=_repository())
        result = use_case.execute(request.user.id)
        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            [_output_to_dict(o) for o in result.value], status=status.HTTP_200_OK
        )

    def post(self, request: Request) -> Response:
        serializer = CreateAccountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = CreateAccountUseCase(repository=_repository())
        result = use_case.execute(
            CreateAccountInput(owner_id=request.user.id, **serializer.to_dto())
        )

        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            _output_to_dict(result.value), status=status.HTTP_201_CREATED
        )


class AccountDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, account_id: int) -> Response:
        use_case = GetAccountUseCase(repository=_repository())
        result = use_case.execute(request.user.id, account_id)
        if not result.is_success:
            code = result.errors[0].code if result.errors else ""
            if code == "accounts.account.not_found":
                return Response(
                    {"detail": result.errors[0].message, "code": code},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )
        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)

    def patch(self, request: Request, account_id: int) -> Response:
        serializer = UpdateAccountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = UpdateAccountUseCase(repository=_repository())
        result = use_case.execute(
            request.user.id, account_id, UpdateAccountInput(**serializer.to_dto())
        )

        if not result.is_success:
            code = result.errors[0].code if result.errors else ""
            if code == "accounts.account.not_found":
                return Response(
                    {"detail": result.errors[0].message, "code": code},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)


class AccountDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, account_id: int) -> Response:
        use_case = DeactivateAccountUseCase(repository=_repository())
        result = use_case.execute(request.user.id, account_id)
        if not result.is_success:
            code = result.errors[0].code if result.errors else ""
            if code == "accounts.account.not_found":
                return Response(
                    {"detail": result.errors[0].message, "code": code},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )
        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)