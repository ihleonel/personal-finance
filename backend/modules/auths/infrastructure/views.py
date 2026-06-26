from __future__ import annotations

from dataclasses import asdict

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.auths.application.dtos import LogoutInput, LoginInput, RegisterInput
from modules.auths.application.use_cases.get_current_user import GetCurrentUserUseCase
from modules.auths.application.use_cases.login_user import LoginUserUseCase
from modules.auths.application.use_cases.logout_user import LogoutUserUseCase
from modules.auths.application.use_cases.register_user import RegisterUserUseCase

from .repositories import DjangoUserRepository
from .serializers import LoginSerializer, LogoutSerializer, RegisterSerializer
from .services import JWTTokenService


def _repository() -> DjangoUserRepository:
    return DjangoUserRepository()


def _token_service() -> JWTTokenService:
    return JWTTokenService()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = RegisterUserUseCase(repository=_repository(), token_service=_token_service())
        output = use_case.execute(RegisterInput(**serializer.to_dto()))

        return Response(
            {"user": asdict(output.user), "tokens": asdict(output.tokens)},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = LoginUserUseCase(repository=_repository(), token_service=_token_service())
        output = use_case.execute(LoginInput(**serializer.to_dto()))

        return Response(
            {"user": asdict(output.user), "tokens": asdict(output.tokens)},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = LogoutUserUseCase(token_service=_token_service())
        use_case.execute(LogoutInput(**serializer.validated_data))

        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        repo = _repository()
        user = repo.find_by_id(request.user.id)
        if user is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        output = GetCurrentUserUseCase().execute(user)
        return Response(asdict(output), status=status.HTTP_200_OK)
