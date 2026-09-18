"""Phoenix Generic Framework event contract."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from phoenix_framework.context import FrameworkContext


@dataclass(frozen=True)
class ModuleEvent:
    """
    Contract representing a fact that something happened.

    Events are published by an owning module and may have zero or more
    subscribers. The publisher does not depend on subscriber behavior.

    FrameworkContext carries the authoritative request, identity, tenant,
    session, permission and entitlement context into the event.
    """

    event_id: str
    event_type: str
    publisher_module: str
    occurred_at: datetime
    context: FrameworkContext
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("Event ID is required.")

        if not self.event_type.strip():
            raise ValueError("Event type is required.")

        if not self.publisher_module.strip():
            raise ValueError("Event publisher module is required.")

        if self.occurred_at.tzinfo is None:
            raise ValueError("Event timestamp must be timezone-aware.")

        self.context.require_authenticated()
        self.context.require_tenant()

    @property
    def request_id(self) -> str:
        """Correlation/request identifier carried by the event."""
        return self.context.request_id

    @property
    def organisation_id(self):
        """Tenant/organisation identifier carried by the event."""
        return self.context.organisation_id

    @property
    def identity_id(self):
        """Originating identity identifier carried by the event."""
        return self.context.identity_id

    @property
    def session_id(self):
        """Originating session identifier carried by the event."""
        return self.context.session_id

    @classmethod
    def create(
        cls,
        event_id: str,
        event_type: str,
        publisher_module: str,
        context: FrameworkContext,
        payload: Mapping[str, Any] | None = None,
    ) -> "ModuleEvent":
        return cls(
            event_id=event_id,
            event_type=event_type,
            publisher_module=publisher_module,
            occurred_at=datetime.now(timezone.utc),
            context=context,
            payload=payload or {},
        )
