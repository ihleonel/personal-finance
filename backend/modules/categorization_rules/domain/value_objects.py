from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


_ALLOWED_MATCH_TYPES = frozenset({"contains", "equals"})
_ALLOWED_RULE_KINDS = frozenset({"income", "expense"})

_MAX_PATTERN_LENGTH = 120

_DIACRITICS_RE = re.compile(r"[\u0300-\u036f]")
_DIGITS_RE = re.compile(r"\d+")
_MULTISPACE_RE = re.compile(r"\s+")


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


def normalize_description(raw: str) -> str:
    """Normaliza una descripción para comparación.

    - lowercase
    - quita diacríticos (acentos)
    - quita secuencias de dígitos (nros. de operación, fechas numéricas)
    - colapsa espacios múltiples
    """
    if not raw:
        return ""
    text = raw.lower()
    text = unicodedata.normalize("NFKD", text)
    text = _DIACRITICS_RE.sub("", text)
    text = _DIGITS_RE.sub(" ", text)
    text = _MULTISPACE_RE.sub(" ", text)
    return text.strip()


allowed_rule_match_types = _ALLOWED_MATCH_TYPES
allowed_rule_kinds = _ALLOWED_RULE_KINDS
max_pattern_length = _MAX_PATTERN_LENGTH