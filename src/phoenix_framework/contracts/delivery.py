"""Phoenix Generic Framework event delivery contract."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, FrozenSet
from uuid import UUID


@dataclass(frozen=True)
class EventDelivery:
    """
    Describes delivery of a module event to a specific subscriber.

    Events represent facts. EventDelivery represents the processing identity
    of delivering that fact to one subscriber while retaining the event
    metadata and security context required for durable delivery.

    The delivery key is stable and may be used as the idempotency key when
    asynchronous delivery is delegated to Phoenix Core Jobs.
    """

    event_id: str
    event_type: str
    publisher_module: str
    occurred_at: datetime
    subscriber_module: str
    request_id: str
    organisation_id: UUID
    identity_id: UUID | None = None
    session_id: UUID | None = None
    permissions: FrozenSet[str] = field(default_factory=frozenset)
    entitlements: FrozenSet[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("Event delivery event_id is required.")

        if not self.event_type.strip():
            raise ValueError("Event delivery event_type is required.")

        if not self.publisher_module.strip():
            raise ValueError(
                "Event delivery publisher_module is required."
            )

        if self.occurred_at.tzinfo is None:
            raise ValueError(
                "Event delivery occurred_at must be timezone-aware."
            )

        if not self.subscriber_module.strip():
            raise ValueError(
                "Event delivery subscriber_module is required."
            )

        if not self.request_id.strip():
            raise ValueError("Event delivery request_id is required.")

        if self.organisation_id is None:
            raise ValueError(
                "Event delivery organisation_id is required."
            )

    @property
    def delivery_key(self) -> str:
        """
        Return the stable identity of this event/subscriber delivery.

        The same event delivered to the same subscriber always produces the
        same key, regardless of delivery attempt count.
        """
        return (
            f"event:{self.event_id}:"
            f"subscriber:{self.subscriber_module.strip().lower()}"
        )

    @classmethod
    def from_event(
        cls,
        event: Any,
        subscriber_module: str,
    ) -> "EventDelivery":
        """Create a delivery identity from a published ModuleEvent."""

        return cls(
            event_id=event.event_id,
            event_type=event.event_type,
            publisher_module=event.publisher_module,
            occurred_at=event.occurred_at,
            subscriber_module=subscriber_module,
            request_id=event.request_id,
            organisation_id=event.organisation_id,
            identity_id=event.identity_id,
            session_id=event.session_id,
            permissions=event.context.permissions,
            entitlements=event.context.entitlements,
        )
