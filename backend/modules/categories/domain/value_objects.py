from __future__ import annotations

from dataclasses import dataclass


_ALLOWED_CATEGORY_KINDS = frozenset({"income", "expense"})


class InvalidCategoryKindError(ValueError):
    pass


@dataclass(frozen=True)
class CategoryKind:
    value: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, str)
            or self.value not in _ALLOWED_CATEGORY_KINDS
        ):
            raise InvalidCategoryKindError(f"Invalid category kind: {self.value!r}")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def try_parse(cls, raw: object) -> "CategoryKind | None":
        if not isinstance(raw, str):
            return None
        try:
            return cls(raw)
        except InvalidCategoryKindError:
            return None


allowed_category_kinds = _ALLOWED_CATEGORY_KINDS