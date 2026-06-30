class CategoriesDomainError(Exception):
    """Base error for the categories domain."""


class CategoryNotFoundError(CategoriesDomainError):
    pass


class CategoryNotOwnedError(CategoriesDomainError):
    pass