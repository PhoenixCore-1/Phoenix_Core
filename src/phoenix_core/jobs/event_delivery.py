"""Phoenix Core adapter for durable event delivery scheduling."""

from phoenix_core.jobs.contracts import JobRequest
from phoenix_core.jobs.service import JobService


class CoreEventDeliveryScheduler:
    """
    Adapts a durable event-delivery scheduling request to Phoenix Core Jobs.

    Core Jobs remains authoritative for persistence, idempotency, retries,
    claiming, execution and lifecycle.

    The adapter deliberately does not import Generic Framework contracts.
    This preserves the dependency direction in which Core remains independent
    of the Generic Framework.

    The request is consumed through its stable scheduling attributes:
    request_id, organisation_id, identity_id, scheduled_at,
    idempotency_key and delivery.
    """

    EVENT_DELIVERY_JOB_TYPE = "framework.event_delivery"

    def __init__(self, job_service: JobService) -> None:
        self.job_service = job_service

    @staticmethod
    def _build_payload(request) -> dict:
        """Build the JSON-safe durable event-delivery envelope."""

        delivery = request.delivery

        return {
            "event_id": delivery.event_id,
            "event_type": delivery.event_type,
            "publisher_module": delivery.publisher_module,
            "occurred_at": delivery.occurred_at.isoformat(),
            "subscriber_module": delivery.subscriber_module,
            "request_id": delivery.request_id,
            "organisation_id": str(delivery.organisation_id),
            "identity_id": (
                str(delivery.identity_id)
                if delivery.identity_id is not None
                else None
            ),
            "session_id": (
                str(delivery.session_id)
                if delivery.session_id is not None
                else None
            ),
            "permissions": sorted(delivery.permissions),
            "entitlements": sorted(delivery.entitlements),
            "event_payload": dict(request.payload or {}),
        }

    def schedule(self, request):
        """Persist a durable event-delivery job through Core Jobs."""

        return self.job_service.enqueue(
            JobRequest(
                request_id=request.request_id,
                job_type=self.EVENT_DELIVERY_JOB_TYPE,
                organisation_id=request.organisation_id,
                identity_id=request.identity_id,
                payload=self._build_payload(request),
                scheduled_at=request.scheduled_at,
                idempotency_key=request.idempotency_key,
            )
        )
