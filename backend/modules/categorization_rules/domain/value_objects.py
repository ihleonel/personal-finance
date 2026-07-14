from __future__ import annotations

from dataclasses import dataclass

from modules.shared.domain.text_utils import normalize_description

__all__ = [
    "normalize_description",
    "RulePattern",
    "RuleMatchType",
    "RuleKind",
    "InvalidRulePatternError",
    "InvalidRuleMatchTypeError",
    "InvalidRuleKindError",
    "allowed_rule_match_types",
    "allowed_rule_kinds",
    "max_pattern_length",
]


_ALLOWED_MATCH_TYPES = frozenset({"contains", "equals"})
_ALLOWED_RULE_KINDS = frozenset({"income", "expense"})

_MAX_PATTERN_LENGTH = 120


class InvalidRulePatternError(ValueError):
    pass


class InvalidRuleMatchTypeError(ValueError):
    pass


class InvalidRuleKindError(ValueError):
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
class RuleKind:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or self.value not in _ALLOWED_RULE_KINDS:
            raise InvalidRuleKindError(f"Tipo de regla inválido: {self.value!r}")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def try_parse(cls, raw: object) -> "RuleKind | None":
        if not isinstance(raw, str):
            return None
        try:
            return cls(raw)
        except InvalidRuleKindError:
            return None


allowed_rule_match_types = _ALLOWED_MATCH_TYPES
allowed_rule_kinds = _ALLOWED_RULE_KINDS
max_pattern_length = _MAX_PATTERN_LENGTH