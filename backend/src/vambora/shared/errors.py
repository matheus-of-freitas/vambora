"""Top-level error hierarchy.

Adapters and application layers raise these (not framework exceptions) so the
HTTP middleware can translate them to status codes consistently.
"""

from vambora.domain.shared.errors import DomainError


class VamboraError(Exception):
    """Root for application-layer and adapter errors."""


class ProviderError(VamboraError):
    """Upstream feed (e.g. SPPO) failed or returned malformed data."""


class PersistenceError(VamboraError):
    """Database operation failed."""


__all__ = ["DomainError", "PersistenceError", "ProviderError", "VamboraError"]
