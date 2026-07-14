from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class CreateTransferDetectionRuleInput:
    owner_id: int
    pattern: str
    match_type: str
    priority: int = 0


@dataclass(frozen=True)
class UpdateTransferDetectionRuleInput:
    pattern: Optional[str] = None
    match_type: Optional[str] = None
    priority: Optional[int] = None


@dataclass(frozen=True)
class TransferDetectionRuleOutput:
    id: int
    owner_id: int
    pattern: str
    match_type: str
    priority: int
    is_active: bool


@dataclass(frozen=True)
class SuggestTransferInput:
    owner_id: int
    description: str


@dataclass(frozen=True)
class SuggestTransferOutput:
    is_transfer: bool


@dataclass(frozen=True)
class DetectTransfersInput:
    owner_id: int
    account_id: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    window_days: int = 3
    amount_tolerance: str = "0.00"


@dataclass(frozen=True)
class TransferPairSuggestionOutput:
    source_id: int
    destination_id: int
    amount: str
    source_account_id: int
    destination_account_id: int
    source_date: str
    destination_date: str
    score: float
    matched_by: str


@dataclass(frozen=True)
class DetectTransfersOutput:
    suggestions: list[TransferPairSuggestionOutput]