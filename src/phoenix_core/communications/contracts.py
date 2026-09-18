"""Contracts for Phoenix internal communications integrations."""

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True)
class RealtimeEvent:
    """Transport-independent communication event."""

    event_type: str
    organisation_id: UUID
    actor_identity_id: UUID
    resource_type: str
    resource_id: UUID
    payload: dict[str, Any]


class RealtimePublisher(Protocol):
    """Port for publishing communications events to a realtime adapter."""

    def publish(self, event: RealtimeEvent) -> None:
        """Publish a communication event."""
        ...
