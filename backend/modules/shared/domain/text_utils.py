from __future__ import annotations

import re
import unicodedata


_DIACRITICS_RE = re.compile(r"[\u0300-\u036f]")
_DIGITS_RE = re.compile(r"\d+")
_MULTISPACE_RE = re.compile(r"\s+")


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