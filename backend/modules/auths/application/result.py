from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class ValidationError:
    field: str
    code: str
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message}


@dataclass
class Result(Generic[T]):
    _value: Optional[T] = None
    _errors: list[ValidationError] = field(default_factory=list)

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        return cls(_value=value, _errors=[])

    @classmethod
    def fail(cls, errors: list[ValidationError]) -> "Result[T]":
        return cls(_value=None, _errors=list(errors))

    @property
    def is_success(self) -> bool:
        return not self._errors and self._value is not None

    @property
    def has_errors(self) -> bool:
        return bool(self._errors)

    @property
    def value(self) -> T:
        if self._value is None:
            raise RuntimeError("Result has no value; check is_success first.")
        return self._value

    @property
    def errors(self) -> list[ValidationError]:
        return list(self._errors)

    def add_error(self, field: str, code: str, message: str) -> None:
        self._errors.append(ValidationError(field, code, message))