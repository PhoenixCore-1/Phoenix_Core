"""Phoenix Generic Framework event delivery scheduling contract."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping
from uuid import UUID

from phoenix_framework.contracts.delivery import EventDelivery


@dataclass(frozen=True)
class EventDeliverySchedule:
    """
    Describes a request to schedule durable processing of an event delivery.

    The Framework defines this contract only. It does not own persistence,
    retries, worker execution, or job lifecycle.
    """

    delivery: EventDelivery
    payload: Mapping[str, Any] | None = None
    scheduled_at: datetime | None = None

    @property
    def idempotency_key(self) -> str:
        """Return the stable Core-compatible delivery idempotency key."""
        return self.delivery.delivery_key

    @property
    def organisation_id(self) -> UUID:
        """Return the tenant carried by the event delivery."""
        return self.delivery.organisation_id

    @property
    def identity_id(self) -> UUID | None:
        """Return the originating identity."""
        return self.delivery.identity_id

    @property
    def request_id(self) -> str:
        """Return the originating request/correlation identifier."""
        return self.delivery.request_id


class EventDeliveryScheduler:
    """
    Port for durable event-delivery scheduling.

    Implementations are supplied by the application composition layer.
    The Framework must not depend directly on Phoenix Core JobService.
    """

    def schedule(
        self,
        request: EventDeliverySchedule,
    ) -> object:
        """Schedule durable processing of an event delivery."""
        raise NotImplementedError
