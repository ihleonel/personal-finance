from __future__ import annotations

from dataclasses import dataclass

from modules.shared.domain.text_utils import normalize_description

__all__ = [
    "RulePattern",
    "RuleMatchType",
    "DateWindowDays",
    "AmountTolerance",
    "normalize_description",
    "InvalidRulePatternError",
    "InvalidRuleMatchTypeError",
    "InvalidDateWindowError",
    "InvalidAmountToleranceError",
    "allowed_rule_match_types",
    "max_pattern_length",
    "default_date_window_days",
    "default_amount_tolerance",
]


_ALLOWED_MATCH_TYPES = frozenset({"contains", "equals"})
_MAX_PATTERN_LENGTH = 120

_DEFAULT_DATE_WINDOW_DAYS = 3
_DEFAULT_AMOUNT_TOLERANCE = "0.00"
_MAX_DATE_WINDOW_DAYS = 30


class InvalidRulePatternError(ValueError):
    pass


class InvalidRuleMatchTypeError(ValueError):
    pass


class InvalidDateWindowError(ValueError):
    pass


class InvalidAmountToleranceError(ValueError):
    pass


@dataclass(frozen=True)
class RulePattern:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise InvalidRulePatternError("El patrón es obligatorio.")
        if len(self.value) > _MAX_PATTERN_LENGTH:
            raise InvalidRulePatternError(
                f"El patrón no puede tener más de {_MAX_PATTERN_LENGTH} caracteres."
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RuleMatchType:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or self.value not in _ALLOWED_MATCH_TYPES:
            raise InvalidRuleMatchTypeError(f"Tipo de match inválido: {self.value!r}")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def try_parse(cls, raw: object) -> "RuleMatchType | None":
        if not isinstance(raw, str):
            return None
        try:
            return cls(raw)
        except InvalidRuleMatchTypeError:
            return None


@dataclass(frozen=True)
class DateWindowDays:
    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or self.value < 0:
            raise InvalidDateWindowError(
                f"La ventana de días debe ser un entero no negativo: {self.value!r}"
            )
        if self.value > _MAX_DATE_WINDOW_DAYS:
            raise InvalidDateWindowError(
                f"La ventana de días no puede superar {_MAX_DATE_WINDOW_DAYS}."
            )

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def try_parse(cls, raw: object) -> "DateWindowDays | None":
        if isinstance(raw, bool) or not isinstance(raw, int):
            return None
        try:
            return cls(raw)
        except InvalidDateWindowError:
            return None


@dataclass(frozen=True)
class AmountTolerance:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidAmountToleranceError(
                f"La tolerancia debe ser una cadena decimal: {self.value!r}"
            )
        try:
            parsed = float(self.value)
        except (TypeError, ValueError):
            raise InvalidAmountToleranceError(
                f"La tolerancia no es un número válido: {self.value!r}"
            )
        if parsed < 0:
            raise InvalidAmountToleranceError(
                f"La tolerancia no puede ser negativa: {self.value!r}"
            )

    def __str__(self) -> str:
        return self.value


allowed_rule_match_types = _ALLOWED_MATCH_TYPES
max_pattern_length = _MAX_PATTERN_LENGTH
default_date_window_days = _DEFAULT_DATE_WINDOW_DAYS
default_amount_tolerance = _DEFAULT_AMOUNT_TOLERANCE