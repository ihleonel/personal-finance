class CategorizationRulesDomainError(Exception):
    """Base error for the categorization_rules domain."""


class CategorizationRuleNotFoundError(CategorizationRulesDomainError):
    pass


class CategorizationRuleNotOwnedError(CategorizationRulesDomainError):
    pass