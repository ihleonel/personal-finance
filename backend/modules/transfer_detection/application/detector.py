from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Iterable, Optional

from modules.shared.domain.text_utils import normalize_description


class TransferCandidateDetector:
    """Matching de descripciones contra reglas de detección de transferencias.

    Recibe las reglas activas del owner (ordenadas por prioridad desc) y una
    descripción de transacción, y devuelve ``True`` si alguna regla coincide
    (es decir, la descripción sugiere que la transacción es una transferencia).

    El matching es análogo al de ``CategorySuggestionService``: normaliza tanto
    la descripción como el patrón (lowercase, sin diacríticos, sin dígitos,
    espacios colapsados) y aplica:
    - ``contains``: el patrón normalizado es subcadena de la descripción.
    - ``equals``: el patrón normalizado coincide exactamente con la desc.
    """

    def is_transfer_candidate(
        self,
        description: str,
        rules: Iterable,
    ) -> bool:
        normalized_desc = normalize_description(description or "")
        if not normalized_desc:
            return False

        for rule in rules:
            if not getattr(rule, "is_active", True):
                continue
            normalized_pattern = normalize_description(rule.pattern or "")
            if not normalized_pattern:
                continue
            if rule.match_type == "equals":
                if normalized_pattern == normalized_desc:
                    return True
            else:
                if normalized_pattern in normalized_desc:
                    return True
        return False


@dataclass(frozen=True)
class TransferPairSuggestion:
    source_id: int
    destination_id: int
    amount: str
    source_account_id: int
    destination_account_id: int
    source_date: date
    destination_date: date
    score: float
    matched_by: str


class TransferPairMatcher:
    """Empareja transacciones income/expense candidatas a transferencia.

    Criterios para emparejar dos transacciones ``a`` (expense) y ``b`` (income):
    - ``transfer_group_id`` es ``None`` en ambas (no están ya vinculadas).
    - cuentas distintas.
    - mismo ``|amount|`` dentro de ``amount_tolerance``.
    - fechas dentro de ``window_days`` de diferencia.
    - (opcional) ambas son candidatas por regla de texto.

    Devuelve una lista de ``TransferPairSuggestion`` ordenada por score desc.
    Cada transacción aparece a lo sumo en un par (matching greedy por score).
    """

    def match(
        self,
        transactions: Iterable,
        window_days: int = 3,
        amount_tolerance: str = "0.00",
        require_both_candidates: bool = False,
        candidate_ids: Optional[set[int]] = None,
    ) -> list[TransferPairSuggestion]:
        txs = list(transactions)
        expenses = [t for t in txs if t.kind == "expense" and t.transfer_group_id is None]
        incomes = [t for t in txs if t.kind == "income" and t.transfer_group_id is None]

        if require_both_candidates and candidate_ids is not None:
            expenses = [t for t in expenses if t.id in candidate_ids]
            incomes = [t for t in incomes if t.id in candidate_ids]

        try:
            tolerance = Decimal(amount_tolerance)
        except (InvalidOperation, TypeError, ValueError):
            tolerance = Decimal("0.00")

        candidates: list[tuple[float, TransferPairSuggestion]] = []
        for exp in expenses:
            for inc in incomes:
                if exp.account_id == inc.account_id:
                    continue
                if exp.owner_id != inc.owner_id:
                    continue
                if abs(exp.amount - inc.amount) > tolerance:
                    continue
                day_diff = abs((exp.date - inc.date).days)
                if day_diff > window_days:
                    continue
                score = self._score(day_diff, exp.amount == inc.amount)
                suggestion = TransferPairSuggestion(
                    source_id=exp.id or 0,
                    destination_id=inc.id or 0,
                    amount=str(exp.amount),
                    source_account_id=exp.account_id,
                    destination_account_id=inc.account_id,
                    source_date=exp.date,
                    destination_date=inc.date,
                    score=score,
                    matched_by="amount+date",
                )
                candidates.append((score, suggestion))

        candidates.sort(key=lambda c: c[0], reverse=True)

        used: set[int] = set()
        result: list[TransferPairSuggestion] = []
        for score, suggestion in candidates:
            if suggestion.source_id in used or suggestion.destination_id in used:
                continue
            used.add(suggestion.source_id)
            used.add(suggestion.destination_id)
            result.append(suggestion)
        return result

    @staticmethod
    def _score(day_diff: int, exact_amount: bool) -> float:
        score = 0.5
        if exact_amount:
            score += 0.3
        if day_diff == 0:
            score += 0.2
        elif day_diff == 1:
            score += 0.1
        return score