from vambora.domain.shared.errors import DomainError


class PredictionError(DomainError):
    """Base for the predictions bounded context."""
