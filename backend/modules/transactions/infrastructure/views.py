from __future__ import annotations

from dataclasses import asdict

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.accounts.infrastructure.repositories import DjangoAccountRepository
from modules.categories.infrastructure.repositories import DjangoCategoryRepository
from modules.categorization_rules.application.categorizer import (
    CategorySuggestionService,
)
from modules.categorization_rules.infrastructure.repositories import (
    DjangoCategorizationRuleRepository,
)
from modules.shared.application.result import ValidationError
from modules.transactions.application.dtos import (
    BulkAssignCategoryInput,
    CreateTransactionInput,
    CreateTransferInput,
    LinkTransferInput,
    ListTransactionsFilters,
    UpdateTransactionInput,
)
from modules.transfer_detection.application.detector import (
    TransferCandidateDetector,
    TransferPairMatcher,
)
from modules.transfer_detection.infrastructure.repositories import (
    DjangoTransferDetectionRuleRepository,
)
from modules.transactions.application.use_cases.create_transaction import (
    CreateTransactionUseCase,
)
from modules.transactions.application.use_cases.create_transfer import (
    CreateTransferUseCase,
)
from modules.transactions.application.use_cases.link_transfer import (
    LinkTransferUseCase,
)
from modules.transactions.application.use_cases.delete_transaction import (
    DeleteTransactionUseCase,
)
from modules.transactions.application.use_cases.get_transaction import (
    GetTransactionUseCase,
)
from modules.transactions.application.use_cases.import_transactions import (
    ImportTransactionsUseCase,
)
from modules.transactions.application.use_cases.list_transactions import (
    ListTransactionsUseCase,
)
from modules.transactions.application.use_cases.update_transaction import (
    UpdateTransactionUseCase,
)
from modules.transactions.application.use_cases.bulk_assign_category import (
    BulkAssignCategoryUseCase,
)

from .repositories import DjangoTransactionRepository
from .serializers import (
    BulkAssignCategorySerializer,
    CreateTransactionSerializer,
    CreateTransferSerializer,
    LinkTransferSerializer,
    ListTransactionsQuerySerializer,
    UpdateTransactionSerializer,
)
from .importers.parsers import AutoTransactionFileParser


def _repository() -> DjangoTransactionRepository:
    return DjangoTransactionRepository()


def _account_repository() -> DjangoAccountRepository:
    return DjangoAccountRepository()


def _category_repository() -> DjangoCategoryRepository:
    return DjangoCategoryRepository()


def _rule_repository() -> DjangoCategorizationRuleRepository:
    return DjangoCategorizationRuleRepository()


def _suggestion_service() -> CategorySuggestionService:
    return CategorySuggestionService()


def _transfer_rule_repository() -> DjangoTransferDetectionRuleRepository:
    return DjangoTransferDetectionRuleRepository()


def _transfer_candidate_detector() -> TransferCandidateDetector:
    return TransferCandidateDetector()


def _transfer_pair_matcher() -> TransferPairMatcher:
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
    if code == "transactions.transaction.not_found":
        return Response(
            {"detail": result.errors[0].message, "code": code},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(_errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST)


class TransactionPagination(PageNumberPagination):
    page_size = 30
    page_query_param = "page"
    page_size_query_param = None
    max_page_size = 100


class TransactionListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = TransactionPagination

    def get(self, request: Request) -> Response:
        serializer = ListTransactionsQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = ListTransactionsUseCase(repository=_repository())
        result = use_case.execute(
            owner_id=request.user.id,
            filters=ListTransactionsFilters(**serializer.to_filters()),
        )
        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(result.value, request, view=self)
        if page is None:
            return paginator.get_paginated_response([])
        return paginator.get_paginated_response(
            [_output_to_dict(o) for o in page]
        )

    def post(self, request: Request) -> Response:
        serializer = CreateTransactionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = CreateTransactionUseCase(
            repository=_repository(),
            account_repository=_account_repository(),
            category_repository=_category_repository(),
        )
        result = use_case.execute(
            CreateTransactionInput(owner_id=request.user.id, **serializer.to_dto())
        )

        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            _output_to_dict(result.value), status=status.HTTP_201_CREATED
        )


class TransferCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = CreateTransferSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = CreateTransferUseCase(
            repository=_repository(),
            account_repository=_account_repository(),
        )
        result = use_case.execute(
            CreateTransferInput(owner_id=request.user.id, **serializer.to_dto())
        )

        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(_output_to_dict(result.value), status=status.HTTP_201_CREATED)


class TransferLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = LinkTransferSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = LinkTransferUseCase(repository=_repository())
        result = use_case.execute(
            LinkTransferInput(owner_id=request.user.id, **serializer.to_dto())
        )

        if not result.is_success:
            code = result.errors[0].code if result.errors else ""
            if code == "transactions.transfer.not_found":
                return Response(
                    {"detail": result.errors[0].message, "code": code},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)


class TransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, transaction_id: int) -> Response:
        use_case = GetTransactionUseCase(repository=_repository())
        result = use_case.execute(request.user.id, transaction_id)
        if not result.is_success:
            return _not_found_response(result)
        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)

    def patch(self, request: Request, transaction_id: int) -> Response:
        serializer = UpdateTransactionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = UpdateTransactionUseCase(
            repository=_repository(),
            category_repository=_category_repository(),
        )
        result = use_case.execute(
            request.user.id,
            transaction_id,
            UpdateTransactionInput(**serializer.to_dto()),
        )

        if not result.is_success:
            return _not_found_response(result)

        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)

    def delete(self, request: Request, transaction_id: int) -> Response:
        use_case = DeleteTransactionUseCase(repository=_repository())
        result = use_case.execute(request.user.id, transaction_id)
        if not result.is_success:
            return _not_found_response(result)
        return Response(status=status.HTTP_204_NO_CONTENT)


_MAX_IMPORT_SIZE = 2 * 1024 * 1024


class TransactionImportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        if "file" not in request.FILES:
            return Response(
                {"file": ["El archivo es obligatorio."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        upload = request.FILES["file"]
        if not upload.name.lower().endswith(".csv"):
            return Response(
                {"file": ["El archivo debe ser un CSV."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if upload.size > _MAX_IMPORT_SIZE:
            return Response(
                {"file": ["El archivo no puede pesar más de 2 MB."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        account_id = request.data.get("account_id")
        if account_id is None:
            return Response(
                {"account_id": ["La cuenta es obligatoria."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            account_id_int = int(account_id)
        except (TypeError, ValueError):
            return Response(
                {"account_id": ["La cuenta no es válida."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        use_case = ImportTransactionsUseCase(
            repository=_repository(),
            account_repository=_account_repository(),
            rule_repository=_rule_repository(),
            suggestion_service=_suggestion_service(),
            transfer_rule_repository=_transfer_rule_repository(),
            transfer_candidate_detector=_transfer_candidate_detector(),
            transfer_pair_matcher=_transfer_pair_matcher(),
        )
        result = use_case.execute(
            owner_id=request.user.id,
            account_id=account_id_int,
            file_bytes=upload.read(),
            filename=upload.name,
            parser=AutoTransactionFileParser(),
        )

        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(asdict(result.value), status=status.HTTP_201_CREATED)


class TransactionBulkAssignCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = BulkAssignCategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        use_case = BulkAssignCategoryUseCase(
            repository=_repository(),
            category_repository=_category_repository(),
        )
        result = use_case.execute(
            BulkAssignCategoryInput(
                owner_id=request.user.id,
                transaction_ids=serializer.validated_data["transaction_ids"],
                category_id=serializer.validated_data.get("category_id"),
            )
        )

        if not result.is_success:
            return Response(
                _errors_to_drf(result.errors), status=status.HTTP_400_BAD_REQUEST
            )

        return Response(_output_to_dict(result.value), status=status.HTTP_200_OK)