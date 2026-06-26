class AuthsDomainError(Exception):
    """Base error for the auths domain."""


class UserAlreadyExistsError(AuthsDomainError):
    pass


class UserNotFoundError(AuthsDomainError):
    pass


class InvalidCredentialsError(AuthsDomainError):
    pass


class InactiveUserError(AuthsDomainError):
    pass
