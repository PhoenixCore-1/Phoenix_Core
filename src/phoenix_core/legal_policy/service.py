from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.legal_policy.domain import (
    Policy,
    PolicyAcceptance,
    PolicyScope,
    PolicyStatus,
    PolicyVersion,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat()


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


class LegalPolicyService:
    """Authoritative Core service for platform legal/policy state."""

    def __init__(self, db: SQLiteDatabase):
        self.db = db

    def create_policy(
        self,
        organisation_id: UUID,
        policy_code: str,
        policy_type: str,
        *,
        required_acceptance: bool = False,
        applicable_scope: PolicyScope = PolicyScope.ORGANISATION,
    ) -> Policy:
        now = _utcnow()
        policy_id = uuid4()

        self.db.execute(
            """
            INSERT INTO policies (
                id,
                organisation_id,
                policy_code,
                policy_type,
                status,
                required_acceptance,
                applicable_scope,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(policy_id),
                str(organisation_id),
                policy_code.strip(),
                policy_type.strip(),
                PolicyStatus.DRAFT.value,
                int(required_acceptance),
                applicable_scope.value,
                _iso(now),
                _iso(now),
            ),
        )
        self.db.commit()

        return Policy(
            id=policy_id,
            organisation_id=organisation_id,
            policy_code=policy_code.strip(),
            policy_type=policy_type.strip(),
            status=PolicyStatus.DRAFT,
            required_acceptance=required_acceptance,
            applicable_scope=applicable_scope,
            created_at=now,
            updated_at=now,
        )

    def add_policy_version(
        self,
        policy_id: UUID,
        version_number: int,
        version_label: str,
        document_id: UUID,
        effective_at: datetime,
        *,
        acceptance_required: bool,
    ) -> PolicyVersion:
        now = _utcnow()
        version_id = uuid4()

        self.db.execute(
            """
            INSERT INTO policy_versions (
                id,
                policy_id,
                version_number,
                version_label,
                document_id,
                effective_at,
                acceptance_required,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(version_id),
                str(policy_id),
                version_number,
                version_label.strip(),
                str(document_id),
                _iso(effective_at),
                int(acceptance_required),
                PolicyStatus.DRAFT.value,
                _iso(now),
            ),
        )
        self.db.commit()

        return PolicyVersion(
            id=version_id,
            policy_id=policy_id,
            version_number=version_number,
            version_label=version_label.strip(),
            document_id=document_id,
            effective_at=effective_at,
            acceptance_required=acceptance_required,
            status=PolicyStatus.DRAFT,
            created_at=now,
        )

    def activate_policy_version(self, policy_version_id: UUID) -> None:
        row = self.db.execute(
            """
            SELECT policy_id
            FROM policy_versions
            WHERE id = ?
            """,
            (str(policy_version_id),),
        ).fetchone()

        if row is None:
            raise ValueError("Policy version not found.")

        self.db.execute(
            """
            UPDATE policy_versions
            SET status = ?
            WHERE id = ?
            """,
            (PolicyStatus.ACTIVE.value, str(policy_version_id)),
        )

        self.db.execute(
            """
            UPDATE policies
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                PolicyStatus.ACTIVE.value,
                _iso(_utcnow()),
                row["policy_id"],
            ),
        )

        self.db.commit()

    def record_acceptance(
        self,
        policy_id: UUID,
        policy_version_id: UUID,
        organisation_id: UUID,
        identity_id: UUID,
        *,
        session_id: UUID | None = None,
        request_id: str | None = None,
        audit_event_id: UUID | None = None,
    ) -> PolicyAcceptance:
        accepted_at = _utcnow()
        acceptance_id = uuid4()

        self.db.execute(
            """
            INSERT INTO policy_acceptances (
                id,
                policy_id,
                policy_version_id,
                organisation_id,
                identity_id,
                session_id,
                request_id,
                accepted_at,
                audit_event_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(acceptance_id),
                str(policy_id),
                str(policy_version_id),
                str(organisation_id),
                str(identity_id),
                str(session_id) if session_id else None,
                request_id,
                _iso(accepted_at),
                str(audit_event_id) if audit_event_id else None,
            ),
        )
        self.db.commit()

        return PolicyAcceptance(
            id=acceptance_id,
            policy_id=policy_id,
            policy_version_id=policy_version_id,
            organisation_id=organisation_id,
            identity_id=identity_id,
            session_id=session_id,
            request_id=request_id,
            accepted_at=accepted_at,
            audit_event_id=audit_event_id,
        )

    def has_accepted(
        self,
        organisation_id: UUID,
        identity_id: UUID,
        policy_version_id: UUID,
    ) -> bool:
        row = self.db.execute(
            """
            SELECT 1
            FROM policy_acceptances
            WHERE organisation_id = ?
              AND identity_id = ?
              AND policy_version_id = ?
            LIMIT 1
            """,
            (
                str(organisation_id),
                str(identity_id),
                str(policy_version_id),
            ),
        ).fetchone()

        return row is not None

    def get_policy(self, policy_id: UUID) -> Policy | None:
        row = self.db.execute(
            """
            SELECT *
            FROM policies
            WHERE id = ?
            """,
            (str(policy_id),),
        ).fetchone()

        if row is None:
            return None

        return Policy(
            id=UUID(row["id"]),
            organisation_id=UUID(row["organisation_id"]),
            policy_code=row["policy_code"],
            policy_type=row["policy_type"],
            status=PolicyStatus(row["status"]),
            required_acceptance=bool(row["required_acceptance"]),
            applicable_scope=PolicyScope(row["applicable_scope"]),
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )

    def get_policy_version(
        self,
        policy_version_id: UUID,
    ) -> PolicyVersion | None:
        row = self.db.execute(
            """
            SELECT *
            FROM policy_versions
            WHERE id = ?
            """,
            (str(policy_version_id),),
        ).fetchone()

        if row is None:
            return None

        return PolicyVersion(
            id=UUID(row["id"]),
            policy_id=UUID(row["policy_id"]),
            version_number=row["version_number"],
            version_label=row["version_label"],
            document_id=UUID(row["document_id"]),
            effective_at=_parse_datetime(row["effective_at"]),
            acceptance_required=bool(row["acceptance_required"]),
            status=PolicyStatus(row["status"]),
            created_at=_parse_datetime(row["created_at"]),
        )
