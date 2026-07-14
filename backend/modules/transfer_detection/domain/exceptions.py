class TransferDetectionDomainError(Exception):
    """Base error for the transfer_detection domain."""


class TransferDetectionRuleNotFoundError(TransferDetectionDomainError):
    pass


class TransferDetectionRuleNotOwnedError(TransferDetectionDomainError):
    pass