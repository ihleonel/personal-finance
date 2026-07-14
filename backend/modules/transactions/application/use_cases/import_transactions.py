from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from django.utils.translation import gettext_lazy as _

from modules.accounts.domain.repositories import AccountRepository
from modules.categorization_rules.application.categorizer import (
    CategorySuggestionService,
)
from modules.categorization_rules.domain.repositories import (
    CategorizationRuleRepository,
)
from modules.shared.application.result import Result
from modules.transactions.application.dtos import (
    ImportSkippedRow,
    ImportSummary,
    ImportTransactionResult,
    TransactionOutput,
    TransferPairRef,
)
from modules.transactions.application.ports import (
    ParsedImport,
    TransactionFileParser,
    UnsupportedImportFormatError,
)
from modules.transactions.domain.repositories import TransactionRepository
from modules.transactions.domain.value_objects import (
    TransactionAmount,
    TransactionDate,
    TransactionKind,
)
from modules.transfer_detection.application.detector import (
    TransferCandidateDetector,
    TransferPairMatcher,
)
from modules.transfer_detection.domain.repositories import (
    TransferDetectionRuleRepository,
)


_MAX_DESCRIPTION_LENGTH = 255


@dataclass
class ImportTransactionsUseCase:
    repository: TransactionRepository
    account_repository: AccountRepository
    rule_repository: Optional[CategorizationRuleRepository] = None
    suggestion_service: Optional[CategorySuggestionService] = None
    transfer_rule_repository: Optional[TransferDetectionRuleRepository] = None
    transfer_candidate_detector: Optional[TransferCandidateDetector] = None
    transfer_pair_matcher: Optional[TransferPairMatcher] = None

    def execute(
        self,
        owner_id: int,
        account_id: int,
        file_bytes: bytes,
        filename: str,
        parser: TransactionFileParser,
    ) -> Result[ImportTransactionResult]:
        result = Result[ImportTransactionResult]()

        account = self.account_repository.find_by_id(account_id)
        if account is None or account.owner_id != owner_id:
            result.add_error(
                "account",
                "transactions.account.not_found",
                str(_("La cuenta no existe o no te pertenece.")),
            )
            return result

        try:
            parsed = parser.parse(file_bytes, filename)
        except UnsupportedImportFormatError:
            result.add_error(
                "file",
                "import.format.unsupported",
                str(_("El formato del archivo no está soportado.")),
            )
            return result

        active_rules = (
            self.rule_repository.list_active_by_owner(owner_id)
            if self.rule_repository is not None
            else []
        )

        active_transfer_rules = (
            self.transfer_rule_repository.list_active_by_owner(owner_id)
            if self.transfer_rule_repository is not None
            else []
        )

        created: list[TransactionOutput] = []
        skipped: list[ImportSkippedRow] = []
        errors: list = []

        for row in parsed.rows:
            kind_value, amount_value, date_value, field_error = self._parse_row(row)
            if field_error is not None:
                errors.append(field_error)
                continue

            existing = self.repository.find_existing(
                owner_id=owner_id,
                account_id=account_id,
                source=parsed.source,
                external_reference=row.external_reference,
                date=date_value,
                amount=amount_value,
                description=row.description,
            )
            if existing is not None:
                skipped.append(
                    ImportSkippedRow(
                        row_number=row.row_number,
                        external_reference=row.external_reference,
                        reason=str(_("duplicada")),
                    )
                )
                continue

            saved = self.repository.save(
                owner_id=owner_id,
                account_id=account_id,
                category_id=None,
                kind=kind_value,  # type: ignore[arg-type]
                amount=amount_value,  # type: ignore[arg-type]
                date=date_value,  # type: ignore[arg-type]
                description=row.description,
                transfer_group_id=None,
                source=parsed.source,
                external_reference=row.external_reference,
            )

            suggested_category_id = self._suggest(owner_id, row.description, active_rules)
            suggested_is_transfer = self._suggest_transfer(
                row.description, active_transfer_rules
            )
            created.append(
                self._to_output(
                    saved,
                    suggested_category_id=suggested_category_id,
                    suggested_is_transfer=suggested_is_transfer,
                )
            )

        self._pair_transfer_suggestions(created)

        total = len(parsed.rows)
        summary = ImportSummary(
            total=total,
            created=len(created),
            skipped=len(skipped),
            errors=len(errors),
        )
        return Result.ok(
            ImportTransactionResult(
                created=created,
                skipped=skipped,
                errors=errors,
                summary=summary,
            )
        )

    def _suggest(
        self,
        owner_id: int,
        description: str,
        active_rules: list,
    ) -> Optional[int]:
        if self.suggestion_service is None or not active_rules:
            return None
        return self.suggestion_service.suggest(description, active_rules)

    def _suggest_transfer(
        self,
        description: str,
        active_transfer_rules: list,
    ) -> bool:
        if self.transfer_candidate_detector is None or not active_transfer_rules:
            return False
        return self.transfer_candidate_detector.is_transfer_candidate(
            description, active_transfer_rules
        )

    def _pair_transfer_suggestions(self, created: list[TransactionOutput]) -> None:
        if self.transfer_pair_matcher is None:
            return
        candidate_ids = {tx.id for tx in created if tx.suggested_is_transfer}
        if not candidate_ids:
            return
        saved_txs = [
            self.repository.find_by_id(tx.id) for tx in created if tx.id
        ]
        saved_txs = [t for t in saved_txs if t is not None]
        suggestions = self.transfer_pair_matcher.match(
            saved_txs,
            require_both_candidates=True,
            candidate_ids=candidate_ids,
        )
        by_id = {tx.id: tx for tx in created}
        for s in suggestions:
            source = by_id.get(s.source_id)
            destination = by_id.get(s.destination_id)
            if source is None or destination is None:
                continue
            by_id[s.source_id] = _replace_output(
                source,
                suggested_transfer_pair=TransferPairRef(
                    source_id=s.source_id, destination_id=s.destination_id
                ),
            )
            by_id[s.destination_id] = _replace_output(
                destination,
                suggested_transfer_pair=TransferPairRef(
                    source_id=s.source_id, destination_id=s.destination_id
                ),
            )
        for idx, tx in enumerate(created):
            created[idx] = by_id[tx.id]

    @staticmethod
    def _parse_row(row) -> tuple[Optional[str], Optional[Decimal], Optional[date], Optional]:
        from modules.transactions.application.dtos import ImportErrorRow

        raw_amount = row.raw_amount.strip()
        negative = raw_amount.startswith("-")
        amount = TransactionAmount.try_parse(raw_amount.lstrip("-").lstrip("+"))
        if amount is None:
            return (
                None,
                None,
                None,
                ImportErrorRow(
                    row_number=row.row_number,
                    field="amount",
                    message=str(_("El monto no es válido.")),
                ),
            )

        parsed_date = TransactionDate.try_parse(row.raw_date.strip())
        if parsed_date is None:
            return (
                None,
                None,
                None,
                ImportErrorRow(
                    row_number=row.row_number,
                    field="date",
                    message=str(_("La fecha no es válida.")),
                ),
            )

        kind = "expense" if negative else "income"
        kind_vo = TransactionKind.try_parse(kind)
        if kind_vo is None:
            return (
                None,
                None,
                None,
                ImportErrorRow(
                    row_number=row.row_number,
                    field="kind",
                    message=str(_("El tipo de transacción no es válido.")),
                ),
            )

        return kind_vo.value, amount.value, parsed_date.value, None

    @staticmethod
    def _to_output(
        tx,
        suggested_category_id: Optional[int] = None,
        suggested_is_transfer: bool = False,
        suggested_transfer_pair: Optional[TransferPairRef] = None,
    ) -> TransactionOutput:
        return TransactionOutput(
            id=tx.id or 0,
            owner_id=tx.owner_id,
            account_id=tx.account_id,
            category_id=tx.category_id,
            kind=tx.kind,
            amount=str(tx.amount),
            date=tx.date.isoformat() if hasattr(tx.date, "isoformat") else str(tx.date),
            description=tx.description,
            transfer_group_id=str(tx.transfer_group_id) if tx.transfer_group_id is not None else None,
            created_at=tx.created_at.isoformat() if hasattr(tx.created_at, "isoformat") else str(tx.created_at),
            suggested_category_id=suggested_category_id,
            suggested_is_transfer=suggested_is_transfer,
            suggested_transfer_pair=suggested_transfer_pair,
        )


def _replace_output(
    output: TransactionOutput,
    suggested_transfer_pair: Optional[TransferPairRef] = None,
) -> TransactionOutput:
    from dataclasses import replace

    return replace(output, suggested_transfer_pair=suggested_transfer_pair)