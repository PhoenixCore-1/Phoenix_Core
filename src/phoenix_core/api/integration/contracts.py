"""Framework-independent Phoenix Core integration contracts."""

from dataclasses import dataclass
from typing import Any, Mapping
from uuid import UUID


@dataclass(frozen=True)
class IntegrationRequest:
    """Canonical request passed into a Core integration contract."""

    request_id: str
    operation: str
    session_id: UUID | None = None
    organisation_id: UUID | None = None
    payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class IntegrationResponse:
    """Canonical response returned by a Core integration contract."""

    request_id: str
    success: bool
    data: Any = None


class CoreIntegrationContract:
    """Stable contract for integrations communicating with Phoenix Core."""

    def handle(self, request: IntegrationRequest) -> IntegrationResponse:
        """Handle an integration request through the Core boundary."""
        raise NotImplementedError
