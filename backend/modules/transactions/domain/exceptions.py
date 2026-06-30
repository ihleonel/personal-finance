class TransactionsDomainError(Exception):
    """Base error for the transactions domain."""


class TransactionNotFoundError(TransactionsDomainError):
    pass


class TransactionNotOwnedError(TransactionsDomainError):
    pass