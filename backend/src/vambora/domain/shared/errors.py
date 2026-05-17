class DomainError(Exception):
    """Root of the domain error hierarchy. All domain failures inherit from this."""


class InvariantViolation(DomainError):
    """Raised when a value object or entity is constructed in an invalid state."""
