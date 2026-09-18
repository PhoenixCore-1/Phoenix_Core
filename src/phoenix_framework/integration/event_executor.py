"""Phoenix Generic Framework durable event-delivery job executor."""

from datetime import datetime
from typing import Any, Mapping
from uuid import UUID

from phoenix_core.jobs.contracts import JobExecutor
from phoenix_framework.context import FrameworkContext
from phoenix_framework.contracts.event import ModuleEvent
from phoenix_framework.integration.events import EventBus


class EventDeliveryExecutor(JobExecutor):
    """
    Reconstructs and executes one durable Framework event delivery.

    Core owns the job lifecycle. The Framework owns event reconstruction and
    subscriber dispatch. Subscriber failures propagate to the Core JobWorker
    so Core can apply its retry/failure lifecycle.
    """

    JOB_TYPE = "framework.event_delivery"

    REQUIRED_FIELDS = (
        "event_id",
        "event_type",
        "publisher_module",
        "occurred_at",
        "subscriber_module",
        "request_id",
        "organisation_id",
        "event_payload",
    )

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus

    def execute(
        self,
        job_type: str,
        payload: Mapping[str, Any] | None,
    ) -> Any:
        """Reconstruct and deliver one durable event."""

        if (job_type or "").strip() != self.JOB_TYPE:
            raise ValueError(
                f"Unsupported event delivery job type: {job_type}"
            )

        envelope = self._validate_payload(payload)

        context = self._build_context(envelope)

        event = ModuleEvent(
            event_id=envelope["event_id"],
            event_type=envelope["event_type"],
            publisher_module=envelope["publisher_module"],
            occurred_at=datetime.fromisoformat(
                envelope["occurred_at"]
            ),
            context=context,
            payload=envelope["event_payload"],
        )

        return self.event_bus.deliver(
            event,
            envelope["subscriber_module"],
        )

    @classmethod
    def _validate_payload(
        cls,
        payload: Mapping[str, Any] | None,
    ) -> Mapping[str, Any]:
        """Validate the durable event envelope."""

        if payload is None:
            raise ValueError(
                "Event delivery job payload is required."
            )

        missing = [
            field
            for field in cls.REQUIRED_FIELDS
            if field not in payload
        ]

        if missing:
            raise ValueError(
                "Event delivery payload is missing required fields: "
                + ", ".join(missing)
            )

        return payload

    @staticmethod
    def _build_context(
        envelope: Mapping[str, Any],
    ) -> FrameworkContext:
        """Reconstruct the Framework security and tenant context."""

        identity_id = envelope.get("identity_id")
        session_id = envelope.get("session_id")

        permissions = envelope.get("permissions", [])
        entitlements = envelope.get("entitlements", [])

        return FrameworkContext(
            request_id=envelope["request_id"],
            identity_id=UUID(identity_id) if identity_id else None,
            organisation_id=UUID(envelope["organisation_id"]),
            session_id=UUID(session_id) if session_id else None,
            permissions=frozenset(permissions),
            entitlements=frozenset(entitlements),
        )
