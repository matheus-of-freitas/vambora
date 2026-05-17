from vambora.domain.shared.errors import DomainError


class TrackingError(DomainError):
    """Base for the tracking bounded context."""
