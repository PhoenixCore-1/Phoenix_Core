"""Core audit application service.

Audit events are append-only Core records. Business modules must use this
service/contract rather than accessing the Core audit table directly.
"""

from datetime import datetime
from uuid import UUID

from phoenix_core.audit.domain import AuditEvent
from phoenix_core.errors import NotFoundError, ValidationError
from phoenix_core.infrastructure import SQLiteDatabase


class AuditService:
    """Owns persistence and tenant-scoped retrieval of Core audit events."""

    def __init__(self, db: SQLiteDatabase):
        self.db = db

    def record(self, event: AuditEvent) -> AuditEvent:
        if event.organisation_id is not None:
            row = self.db.execute(
                "SELECT id FROM organisations WHERE id=?",
                (str(event.organisation_id),),
            ).fetchone()
            if not row:
                raise ValidationError("Audit organisation does not exist.")

        if event.identity_id is not None:
            row = self.db.execute(
                "SELECT id FROM identities WHERE id=?",
                (str(event.identity_id),),
            ).fetchone()
            if not row:
                raise ValidationError("Audit identity does not exist.")

        self.db.execute(
            """
            INSERT INTO audit_events
            (id,organisation_id,identity_id,action,target_type,target_id,request_id,created_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                str(event.id),
                str(event.organisation_id) if event.organisation_id else None,
                str(event.identity_id) if event.identity_id else None,
                event.action,
                event.target_type,
                str(event.target_id) if event.target_id else None,
                event.request_id,
                event.created_at.isoformat(),
            ),
        )
        self.db.commit()
        return event

    def get(self, event_id: UUID) -> AuditEvent:
        row = self.db.execute(
            """
            SELECT id, organisation_id, identity_id, action, target_type,
                   target_id, request_id, created_at
            FROM audit_events
            WHERE id=?
            """,
            (str(event_id),),
        ).fetchone()
        if not row:
            raise NotFoundError("Audit event not found.")
        return self._from_row(row)

    def list(
        self,
        *,
        organisation_id: UUID | None = None,
        identity_id: UUID | None = None,
        action: str | None = None,
        target_type: str | None = None,
        target_id: UUID | None = None,
        request_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        if limit < 1 or limit > 500:
            raise ValidationError("Audit limit must be between 1 and 500.")
        if offset < 0:
            raise ValidationError("Audit offset cannot be negative.")

        clauses = []
        params: list[str | int] = []

        if organisation_id is not None:
            clauses.append("organisation_id=?")
            params.append(str(organisation_id))
        if identity_id is not None:
            clauses.append("identity_id=?")
            params.append(str(identity_id))
        if action is not None:
            clauses.append("action=?")
            params.append(action)
        if target_type is not None:
            clauses.append("target_type=?")
            params.append(target_type)
        if target_id is not None:
            clauses.append("target_id=?")
            params.append(str(target_id))
        if request_id is not None:
            clauses.append("request_id=?")
            params.append(request_id)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.db.execute(
            f"""
            SELECT id, organisation_id, identity_id, action, target_type,
                   target_id, request_id, created_at
            FROM audit_events
            {where}
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row) -> AuditEvent:
        return AuditEvent(
            id=UUID(row["id"]),
            organisation_id=UUID(row["organisation_id"]) if row["organisation_id"] else None,
            identity_id=UUID(row["identity_id"]) if row["identity_id"] else None,
            action=row["action"],
            target_type=row["target_type"],
            target_id=UUID(row["target_id"]) if row["target_id"] else None,
            request_id=row["request_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
