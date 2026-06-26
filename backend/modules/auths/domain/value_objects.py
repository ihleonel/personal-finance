from __future__ import annotations

import re
from dataclasses import dataclass


_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class InvalidEmailError(ValueError):
    pass


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not _EMAIL_RE.match(self.value):
            raise InvalidEmailError(f"Invalid email address: {self.value!r}")

    def __str__(self) -> str:
        return self.value
