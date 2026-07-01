"""Sentinel para distinguir "campo no enviado" de "campo enviado como None".

En los use cases de actualización parcial (PATCH), necesitamos diferenciar
entre un campo que el cliente no incluyó en el payload (no debe modificarse)
y un campo que el cliente envió explícitamente como ``null`` (debe borrarse).
``Optional[T] = None`` no alcanza para eso, porque colapsa ambos casos en
``None``. Usamos ``UNSET`` como valor por defecto y lo comparamos con ``is``.
"""

from __future__ import annotations

from typing import Any

UNSET: Any = object()


def is_set(value: Any) -> bool:
    return value is not UNSET