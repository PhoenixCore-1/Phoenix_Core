from uuid import UUID

from phoenix_core.ai.contracts import AIActionRequest
from phoenix_core.audit.domain import AuditEvent
from phoenix_core.audit.service import AuditService
from phoenix_core.security.context import RequestContext


class AIAuditService:
    """AI audit adapter over the authoritative Core AuditService.

    This service does not own audit persistence. It translates AI lifecycle
    events into Core AuditEvent records.
    """

    AI_REQUESTED = "AI_REQUESTED"
    AI_COMPLETED = "AI_COMPLETED"
    AI_FAILED = "AI_FAILED"
    AI_ACTION_PROPOSED = "AI_ACTION_PROPOSED"
    AI_ACTION_AUTHORIZED = "AI_ACTION_AUTHORIZED"
    AI_ACTION_EXECUTED = "AI_ACTION_EXECUTED"
    AI_QUOTA_EXCEEDED = "AI_QUOTA_EXCEEDED"
    AI_RATE_LIMITED = "AI_RATE_LIMITED"

    def __init__(self, audit_service: AuditService):
        self.audit_service = audit_service

    def record(
        self,
        context: RequestContext,
        action: str,
        *,
        target_type: str | None = None,
        target_id: UUID | None = None,
    ) -> AuditEvent:
        event = AuditEvent.create(
            action=action,
            organisation_id=context.organisation_id,
            identity_id=context.identity_id,
            target_type=target_type or "AI",
            target_id=target_id,
            request_id=context.request_id,
        )

        return self.audit_service.record(event)

    def request_started(
        self,
        context: RequestContext,
    ) -> AuditEvent:
        return self.record(
            context,
            self.AI_REQUESTED,
        )

    def request_completed(
        self,
        context: RequestContext,
    ) -> AuditEvent:
        return self.record(
            context,
            self.AI_COMPLETED,
        )

    def request_failed(
        self,
        context: RequestContext,
    ) -> AuditEvent:
        return self.record(
            context,
            self.AI_FAILED,
        )

    def action_proposed(
        self,
        context: RequestContext,
        action: AIActionRequest,
    ) -> AuditEvent:
        return self.record(
            context,
            self.AI_ACTION_PROPOSED,
            target_type=action.target_type or "AI_ACTION",
            target_id=(
                UUID(action.target_id)
                if action.target_id
                else None
            ),
        )

    def action_authorized(
        self,
        context: RequestContext,
        action: AIActionRequest,
    ) -> AuditEvent:
        return self.record(
            context,
            self.AI_ACTION_AUTHORIZED,
            target_type=action.target_type or "AI_ACTION",
            target_id=(
                UUID(action.target_id)
                if action.target_id
                else None
            ),
        )

    def action_executed(
        self,
        context: RequestContext,
        action: AIActionRequest,
    ) -> AuditEvent:
        return self.record(
            context,
            self.AI_ACTION_EXECUTED,
            target_type=action.target_type or "AI_ACTION",
            target_id=(
                UUID(action.target_id)
                if action.target_id
                else None
            ),
        )

    def quota_exceeded(
        self,
        context: RequestContext,
    ) -> AuditEvent:
        return self.record(
            context,
            self.AI_QUOTA_EXCEEDED,
        )

    def rate_limited(
        self,
        context: RequestContext,
    ) -> AuditEvent:
        return self.record(
            context,
            self.AI_RATE_LIMITED,
        )
