from __future__ import annotations

from typing import Iterable, Optional

from modules.categorization_rules.domain.value_objects import normalize_description


class CategorySuggestionService:
    """Servicio puro de matching de descripciones contra reglas.

    Recibe las reglas activas del owner (ordenadas por prioridad desc) y una
    descripción de transacción, y devuelve el ``category_id`` de la primera
    regla que coincida, o ``None`` si ninguna matchea.

    El matching normaliza tanto la descripción como el patrón (lowercase,
    sin diacríticos, sin dígitos, espacios colapsados) y aplica:
    - ``contains``: el patrón normalizado es subcadena de la descripción.
    - ``equals``: el patrón normalizado coincide exactamente con la desc.
    """

    def suggest(
        self,
        description: str,
        rules: Iterable,
    ) -> Optional[int]:
        normalized_desc = normalize_description(description or "")
        if not normalized_desc:
            return None

        for rule in rules:
            if not getattr(rule, "is_active", True):
                continue
            normalized_pattern = normalize_description(rule.pattern or "")
            if not normalized_pattern:
                continue
            if rule.match_type == "equals":
                if normalized_pattern == normalized_desc:
                    return rule.category_id
            else:
                if normalized_pattern in normalized_desc:
                    return rule.category_id
        return None