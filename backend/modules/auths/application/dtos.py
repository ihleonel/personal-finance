from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterInput:
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""


@dataclass(frozen=True)
class LoginInput:
    email: str
    password: str


@dataclass(frozen=True)
class LogoutInput:
    refresh: str


@dataclass(frozen=True)
class UserOutput:
    id: int
    email: str
    first_name: str
    last_name: str
    is_active: bool


@dataclass(frozen=True)
class AuthTokensOutput:
    access: str
    refresh: str


@dataclass(frozen=True)
class RegisterOutput:
    user: UserOutput
    tokens: AuthTokensOutput


@dataclass(frozen=True)
class LoginOutput:
    user: UserOutput
    tokens: AuthTokensOutput
