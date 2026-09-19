
"""Phoenix Core Legal Compliance service."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4


class LegalComplianceError(Exception):
    """Base legal compliance service error."""


class LegalRequirementNotFound(LegalComplianceError):
    pass


class LegalAssignmentNotFound(LegalComplianceError):
    pass


class LegalValidationError(LegalComplianceError):
    pass


class LegalAuthorizationError(LegalComplianceError):
    pass


class LegalComplianceService:
    """Server-side legal requirement, assignment and evidence operations.

    The service deliberately uses the existing Core database structures for:
    - organisations
    - identities
    - memberships
    - documents
    - document versions

    It does not create a second authentication or document system.
    """

    VALID_ACTIONS = {"ACCEPT", "SIGN", "ACKNOWLEDGE", "CONSENT"}
    VALID_SCOPES = {"COMPANY", "USER"}
    VALID_ENFORCEMENT = {
        "NOTICE_ONLY",
        "REQUIRE_ACTION",
        "RESTRICT_FEATURE",
        "SUSPEND_SERVICE",
    }

    def __init__(self, db):
        self.db = db

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _id() -> str:
        return str(uuid4())

    def create_requirement(
        self,
        *,
        requirement_code: str,
        name: str,
        document_id: UUID,
        document_version_id: UUID,
        action_type: str,
        scope: str,
        enforcement: str = "NOTICE_ONLY",
        description: str | None = None,
        jurisdiction: str | None = None,
        required: bool = True,
        effective_from: str | None = None,
        due_at: str | None = None,
    ) -> dict:
        """Create a draft legal requirement."""

        if action_type not in self.VALID_ACTIONS:
            raise LegalValidationError("Invalid legal action type.")

        if scope not in self.VALID_SCOPES:
            raise LegalValidationError("Invalid legal requirement scope.")

        if enforcement not in self.VALID_ENFORCEMENT:
            raise LegalValidationError("Invalid legal enforcement.")

        document = self.db.execute(
            "SELECT id FROM documents WHERE id=? AND status='ACTIVE'",
            (str(document_id),),
        ).fetchone()

        if not document:
            raise LegalValidationError("Active legal document not found.")

        version = self.db.execute(
            """
            SELECT id, document_id, checksum
            FROM document_versions
            WHERE id=? AND document_id=?
            """,
            (str(document_version_id), str(document_id)),
        ).fetchone()

        if not version:
            raise LegalValidationError(
                "Document version does not belong to the selected document."
            )

        requirement_id = self._id()
        now = self._now()

        self.db.execute(
            """
            INSERT INTO legal_requirements (
                id,
                requirement_code,
                name,
                description,
                document_id,
                document_version_id,
                action_type,
                scope,
                enforcement,
                jurisdiction,
                required,
                effective_from,
                due_at,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', ?, ?)
            """,
            (
                requirement_id,
                requirement_code,
                name,
                description,
                str(document_id),
                str(document_version_id),
                action_type,
                scope,
                enforcement,
                jurisdiction,
                1 if required else 0,
                effective_from,
                due_at,
                now,
                now,
            ),
        )
        self.db.commit()

        return self.get_requirement(UUID(requirement_id))

    def get_requirement(self, requirement_id: UUID) -> dict:
        row = self.db.execute(
            """
            SELECT *
            FROM legal_requirements
            WHERE id=?
            """,
            (str(requirement_id),),
        ).fetchone()

        if not row:
            raise LegalRequirementNotFound("Legal requirement not found.")

        return dict(row)

    def activate_requirement(self, requirement_id: UUID) -> dict:
        """Activate a requirement after validating its document version."""

        requirement = self.get_requirement(requirement_id)

        version = self.db.execute(
            """
            SELECT id, document_id, checksum
            FROM document_versions
            WHERE id=? AND document_id=?
            """,
            (
                requirement["document_version_id"],
                requirement["document_id"],
            ),
        ).fetchone()

        if not version:
            raise LegalValidationError(
                "The requirement's document version no longer exists."
            )

        self.db.execute(
            """
            UPDATE legal_requirements
            SET status='ACTIVE', updated_at=?
            WHERE id=?
            """,
            (self._now(), str(requirement_id)),
        )
        self.db.commit()

        return self.get_requirement(requirement_id)

    def retire_requirement(self, requirement_id: UUID) -> dict:
        self.get_requirement(requirement_id)

        self.db.execute(
            """
            UPDATE legal_requirements
            SET status='RETIRED', updated_at=?
            WHERE id=?
            """,
            (self._now(), str(requirement_id)),
        )
        self.db.commit()

        return self.get_requirement(requirement_id)

    def assign_requirement(
        self,
        requirement_id: UUID,
        *,
        organisation_id: UUID,
        identity_id: UUID | None = None,
        due_at: str | None = None,
    ) -> dict:
        """Assign an active requirement to a company or company user."""

        requirement = self.get_requirement(requirement_id)

        if requirement["status"] != "ACTIVE":
            raise LegalValidationError(
                "Only ACTIVE legal requirements can be assigned."
            )

        expected_scope = requirement["scope"]

        if expected_scope == "COMPANY" and identity_id is not None:
            raise LegalValidationError(
                "Company requirements cannot be assigned to an individual identity."
            )

        if expected_scope == "USER" and identity_id is None:
            raise LegalValidationError(
                "User requirements require an identity."
            )

        organisation = self.db.execute(
            "SELECT id FROM organisations WHERE id=?",
            (str(organisation_id),),
        ).fetchone()

        if not organisation:
            raise LegalValidationError("Organisation not found.")

        if identity_id is not None:
            membership = self.db.execute(
                """
                SELECT identity_id
                FROM organisation_memberships
                WHERE organisation_id=?
                  AND identity_id=?
                  AND status='ACTIVE'
                """,
                (str(organisation_id), str(identity_id)),
            ).fetchone()

            if not membership:
                raise LegalAuthorizationError(
                    "Identity is not an active member of the organisation."
                )

        existing = self.db.execute(
            """
            SELECT id
            FROM legal_requirement_assignments
            WHERE requirement_id=?
              AND organisation_id=?
              AND (
                    (assignment_scope='COMPANY' AND ? IS NULL)
                    OR
                    (assignment_scope='USER' AND identity_id=?)
                  )
            """,
            (
                str(requirement_id),
                str(organisation_id),
                str(identity_id) if identity_id else None,
                str(identity_id) if identity_id else None,
            ),
        ).fetchone()

        if existing:
            raise LegalValidationError(
                "This legal requirement is already assigned."
            )

        assignment_id = self._id()
        now = self._now()

        self.db.execute(
            """
            INSERT INTO legal_requirement_assignments (
                id,
                requirement_id,
                organisation_id,
                identity_id,
                assignment_scope,
                status,
                assigned_at,
                due_at,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, 'ASSIGNED', ?, ?, ?, ?)
            """,
            (
                assignment_id,
                str(requirement_id),
                str(organisation_id),
                str(identity_id) if identity_id else None,
                expected_scope,
                now,
                due_at or requirement["due_at"],
                now,
                now,
            ),
        )
        self.db.commit()

        return self.get_assignment(UUID(assignment_id))

    def get_assignment(self, assignment_id: UUID) -> dict:
        row = self.db.execute(
            """
            SELECT
                a.*,
                r.requirement_code,
                r.name,
                r.action_type,
                r.enforcement,
                r.document_id,
                r.document_version_id
            FROM legal_requirement_assignments a
            JOIN legal_requirements r
              ON r.id=a.requirement_id
            WHERE a.id=?
            """,
            (str(assignment_id),),
        ).fetchone()

        if not row:
            raise LegalAssignmentNotFound("Legal requirement assignment not found.")

        return dict(row)

    def get_required_actions(
        self,
        *,
        organisation_id: UUID,
        identity_id: UUID | None = None,
    ) -> list[dict]:
        """Return actionable legal requirements for the supplied Core context."""

        params: list[str] = [str(organisation_id)]
        identity_clause = ""

        if identity_id is not None:
            identity_clause = """
                OR (
                    a.assignment_scope='USER'
                    AND a.identity_id=?
                )
            """
            params.append(str(identity_id))

        rows = self.db.execute(
            f"""
            SELECT
                a.id AS assignment_id,
                a.requirement_id,
                a.assignment_scope,
                a.status AS assignment_status,
                a.assigned_at,
                a.due_at,
                r.requirement_code,
                r.name,
                r.description,
                r.action_type,
                r.enforcement,
                r.jurisdiction,
                r.document_id,
                r.document_version_id,
                dv.checksum AS document_checksum
            FROM legal_requirement_assignments a
            JOIN legal_requirements r
              ON r.id=a.requirement_id
            JOIN document_versions dv
              ON dv.id=r.document_version_id
            WHERE r.status='ACTIVE'
              AND a.status='ASSIGNED'
              AND (
                    (
                        a.assignment_scope='COMPANY'
                        AND a.organisation_id=?
                    )
                    {identity_clause}
                  )
            ORDER BY
                CASE WHEN a.due_at IS NULL THEN 1 ELSE 0 END,
                a.due_at,
                r.name
            """,
            tuple(params),
        ).fetchall()

        return [dict(row) for row in rows]

    def complete_action(
        self,
        assignment_id: UUID,
        *,
        organisation_id: UUID,
        identity_id: UUID,
        action_type: str,
        document_version_id: UUID,
        document_checksum: str,
        confirmation_reference: str | None = None,
        signature_provider: str | None = None,
        signature_reference: str | None = None,
        technical_evidence: str | None = None,
        audit_event_id: UUID | None = None,
    ) -> dict:
        """Complete an assigned legal action and create immutable evidence."""

        if action_type not in self.VALID_ACTIONS:
            raise LegalValidationError("Invalid legal action type.")

        assignment = self.get_assignment(assignment_id)

        if assignment["organisation_id"] != str(organisation_id):
            raise LegalAuthorizationError(
                "Legal assignment does not belong to the current organisation."
            )

        if assignment["assignment_scope"] == "USER":
            if assignment["identity_id"] != str(identity_id):
                raise LegalAuthorizationError(
                    "Legal assignment does not belong to the current identity."
                )

            membership = self.db.execute(
                """
                SELECT identity_id
                FROM organisation_memberships
                WHERE organisation_id=?
                  AND identity_id=?
                  AND status='ACTIVE'
                """,
                (str(organisation_id), str(identity_id)),
            ).fetchone()

            if not membership:
                raise LegalAuthorizationError(
                    "Identity is not an active member of the organisation."
                )

        requirement = self.get_requirement(
            UUID(assignment["requirement_id"])
        )

        if requirement["status"] != "ACTIVE":
            raise LegalValidationError(
                "The legal requirement is not active."
            )

        if requirement["action_type"] != action_type:
            raise LegalValidationError(
                "Submitted action does not match the requirement."
            )

        if assignment["status"] != "ASSIGNED":
            raise LegalValidationError(
                "This legal assignment has already been processed."
            )

        if requirement["document_version_id"] != str(document_version_id):
            raise LegalValidationError(
                "The submitted document version does not match the requirement."
            )

        version = self.db.execute(
            """
            SELECT checksum
            FROM document_versions
            WHERE id=? AND document_id=?
            """,
            (
                str(document_version_id),
                requirement["document_id"],
            ),
        ).fetchone()

        if not version:
            raise LegalValidationError(
                "Required document version was not found."
            )

        if version["checksum"] != document_checksum:
            raise LegalValidationError(
                "Document checksum does not match the authoritative version."
            )

        if not version["checksum"]:
            raise LegalValidationError(
                "Authoritative document version has no checksum."
            )

        evidence_id = self._id()
        now = self._now()

        self.db.execute(
            """
            INSERT INTO legal_acceptance_evidence (
                id,
                requirement_id,
                assignment_id,
                organisation_id,
                identity_id,
                document_id,
                document_version_id,
                document_checksum,
                action_type,
                completed_at,
                confirmation_reference,
                signature_provider,
                signature_reference,
                technical_evidence,
                audit_event_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                assignment["requirement_id"],
                assignment_id.__str__(),
                str(organisation_id),
                str(identity_id),
                requirement["document_id"],
                str(document_version_id),
                document_checksum,
                action_type,
                now,
                confirmation_reference,
                signature_provider,
                signature_reference,
                technical_evidence,
                str(audit_event_id) if audit_event_id else None,
                now,
            ),
        )

        self.db.execute(
            """
            UPDATE legal_requirement_assignments
            SET status='COMPLETED',
                completed_at=?,
                updated_at=?
            WHERE id=?
              AND status='ASSIGNED'
            """,
            (now, now, str(assignment_id)),
        )

        self.db.commit()

        row = self.db.execute(
            """
            SELECT *
            FROM legal_acceptance_evidence
            WHERE id=?
            """,
            (evidence_id,),
        ).fetchone()

        return dict(row)

    def decline_action(
        self,
        assignment_id: UUID,
        *,
        organisation_id: UUID,
        identity_id: UUID,
    ) -> dict:
        """Record a declined action without creating acceptance evidence."""

        assignment = self.get_assignment(assignment_id)

        if assignment["organisation_id"] != str(organisation_id):
            raise LegalAuthorizationError(
                "Legal assignment does not belong to the current organisation."
            )

        if (
            assignment["assignment_scope"] == "USER"
            and assignment["identity_id"] != str(identity_id)
        ):
            raise LegalAuthorizationError(
                "Legal assignment does not belong to the current identity."
            )

        if assignment["status"] != "ASSIGNED":
            raise LegalValidationError(
                "This legal assignment has already been processed."
            )

        now = self._now()

        self.db.execute(
            """
            UPDATE legal_requirement_assignments
            SET status='DECLINED',
                updated_at=?
            WHERE id=?
              AND status='ASSIGNED'
            """,
            (now, str(assignment_id)),
        )
        self.db.commit()

        return self.get_assignment(assignment_id)
