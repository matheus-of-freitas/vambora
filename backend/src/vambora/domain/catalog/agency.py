from __future__ import annotations

from dataclasses import dataclass

from vambora.domain.shared.errors import InvariantViolation


@dataclass(frozen=True, slots=True)
class Agency:
    agency_id: str
    name: str
    url: str
    timezone: str
    lang: str | None

    def __post_init__(self) -> None:
        if not self.agency_id:
            raise InvariantViolation("agency_id required")
        if not self.name:
            raise InvariantViolation("agency name required")
        if not self.timezone:
            raise InvariantViolation("agency timezone required")
