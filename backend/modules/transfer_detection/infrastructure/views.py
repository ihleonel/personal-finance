from __future__ import annotations

from dataclasses import asdict

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.shared.application.result import ValidationError
from modules.transactions.infrastructure.repositories import (
    DjangoTransactionRepository,
)
from modules.transfer_detection.application.detector import (
    TransferCandidateDetector,
    TransferPairMatcher,
)
from modules.transfer_detection.application.dtos import (
    CreateTransferDetectionRuleInput,
    DetectTransfersInput,
    SuggestTransferInput,
    UpdateTransferDetectionRuleInput,
)
from modules.transfer_detection.application.ports import TransactionQueryPort
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
from modules.transfer_detection.application.use_cases.detect_transfers import (
    DetectTransfersUseCase,
)
from modules.transfer_detection.application.use_cases.get_rule import (
    GetTransferDetectionRuleUseCase,
)
from modules.transfer_detection.application.use_cases.list_rules import (
    ListTransferDetectionRulesUseCase,
)
from modules.transfer_detection.application.use_cases.suggest_transfer import (
    SuggestTransferUseCase,
)
from modules.transfer_detection.application.use_cases.update_rule import (
    UpdateTransferDetectionRuleUseCase,
)
from modules.transfer_detection.infrastructure.repositories import (
    DjangoTransferDetectionRuleRepository,
)
from modules.transfer_detection.infrastructure.serializers import (
    CreateTransferDetectionRuleSerializer,
    DetectTransfersSerializer,
    SuggestTransferSerializer,
    UpdateTransferDetectionRuleSerializer,
)
from modules.transfer_detection.infrastructure.transaction_query_adapter import (
    DjangoTransactionQueryAdapter,
)


def _repository() -> DjangoTransferDetectionRuleRepository:
    return DjangoTransferDetectionRuleRepository()


def _transaction_query() -> TransactionQueryPort:
    return DjangoTransactionQueryAdapter(DjangoTransactionRepository())


def _candidate_detector() -> TransferCandidateDetector:
    return TransferCandidateDetector()


def _pair_matcher() -> TransferPairMatcher:
    return TransferPairMatcher()


def _errors_to_drf(errors: list[ValidationError]) -> dict:
    out: dict[str, list[str]] = {}
    for e in errors:
        out.setdefault(e.field, []).append(e.message)
    return out


def _output_to_dict(output) -> dict:
    return asdict(output)


def _not_found_response(result) -> Response:
    code = result.errors[0].code if result.errors else ""
    if code == "transfer_detection.rule.not_found":
        return Response(
            {"detail": result.errors[0].message, "code": code},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(_errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST)


class TransferDetectionRuleListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        use_case = ListTransferDetectionRulesUseCase(repository=_repository())
        result = use_case.execute(request.user.id)
        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            [_output_to_dict(o) for o in result.value], status=status.HTTP_200_OK
        )

    def post(self, request: Request) -> Response:
        serializer = CreateTransferDetectionRuleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = CreateTransferDetectionRuleUseCase(repository=_repository())
        result = use_case.execute(
            CreateTransferDetectionRuleInput(
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


class TransferDetectionRuleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, rule_id: int) -> Response:
        use_case = GetTransferDetectionRuleUseCase(repository=_repository())
        result = use_case.execute(request.user.id, rule_id)
        if not result.is_success:
            return _not_found_response(result)
        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)

    def patch(self, request: Request, rule_id: int) -> Response:
        serializer = UpdateTransferDetectionRuleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = UpdateTransferDetectionRuleUseCase(repository=_repository())
        result = use_case.execute(
            request.user.id,
            rule_id,
            UpdateTransferDetectionRuleInput(**serializer.to_dto()),
        )

        if not result.is_success:
            return _not_found_response(result)

        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)

    def delete(self, request: Request, rule_id: int) -> Response:
        use_case = DeleteTransferDetectionRuleUseCase(repository=_repository())
        result = use_case.execute(request.user.id, rule_id)
        if not result.is_success:
            return _not_found_response(result)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TransferDetectionRuleDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, rule_id: int) -> Response:
        use_case = DeactivateTransferDetectionRuleUseCase(repository=_repository())
        result = use_case.execute(request.user.id, rule_id)
        if not result.is_success:
            return _not_found_response(result)
        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)


class TransferDetectionRuleActivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, rule_id: int) -> Response:
        use_case = ActivateTransferDetectionRuleUseCase(repository=_repository())
        result = use_case.execute(request.user.id, rule_id)
        if not result.is_success:
            return _not_found_response(result)
        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)


class SuggestTransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = SuggestTransferSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = SuggestTransferUseCase(
            rule_repository=_repository(),
            candidate_detector=_candidate_detector(),
        )
        result = use_case.execute(
            SuggestTransferInput(
                owner_id=request.user.id, **serializer.to_dto()
            )
        )

        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)


class DetectTransfersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = DetectTransfersSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = DetectTransfersUseCase(
            transaction_query=_transaction_query(),
            rule_repository=_repository(),
            candidate_detector=_candidate_detector(),
            pair_matcher=_pair_matcher(),
        )
        result = use_case.execute(
            DetectTransfersInput(
                owner_id=request.user.id, **serializer.to_dto()
            )
        )

        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)