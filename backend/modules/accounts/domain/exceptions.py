class AccountsDomainError(Exception):
    """Base error for the accounts domain."""


class AccountNotFoundError(AccountsDomainError):
    pass


class AccountNotOwnedError(AccountsDomainError):
    pass