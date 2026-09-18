"""Company Platform compliance evidence application service.

Evidence is a tenant-scoped operational record. The referenced document,
version, policy and audit authorities remain in Phoenix Core.
"""

from datetime import datetime, timezone
from uuid import uuid4

from phoenix_core.api.contracts import ApiResponse
from phoenix_core.audit.domain import AuditEvent


class CompanyEvidenceApplicationService:
    def __init__(self, core_api):
        self.core_api = core_api
        self.core = core_api.core_service

    def list_evidence(self, context, *, status=None) -> ApiResponse:
        self.core_api.require_permission(context, "company.reports.view")
        sql = """
            SELECT id, organisation_id, policy_version_id, document_id,
                   document_version_id, evidence_type, title, description,
                   status, valid_from, valid_until, created_by_identity_id,
                   created_at, updated_at
            FROM company_compliance_evidence
            WHERE organisation_id = ?
        """
        params = [str(context.organisation_id)]
        if status:
            sql += " AND status = ?"
            params.append(status.upper())
        sql += " ORDER BY CASE WHEN valid_until IS NULL THEN 1 ELSE 0 END, valid_until, created_at DESC"
        rows = self.core.db.execute(sql, tuple(params)).fetchall()
        items = [dict(row) for row in rows]
        return ApiResponse(
            data={"organisation_id": str(context.organisation_id), "items": items},
            request_id=context.request_id,
        )

    def create_evidence(self, context, *, title, evidence_type, description=None,
                        policy_version_id=None, document_id=None,
                        document_version_id=None, valid_from=None, valid_until=None) -> ApiResponse:
        self.core_api.require_permission(context, "company.configuration.manage")
        evidence_id = uuid4()
        now = datetime.now(timezone.utc).isoformat()
        self.core.db.execute(
            """
            INSERT INTO company_compliance_evidence
            (id, organisation_id, policy_version_id, document_id, document_version_id,
             evidence_type, title, description, status, valid_from, valid_until,
             created_by_identity_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, ?, ?)
            """,
            (str(evidence_id), str(context.organisation_id), policy_version_id,
             document_id, document_version_id, evidence_type.strip().upper(),
             title.strip(), description, valid_from, valid_until,
             str(context.identity_id), now, now),
        )
        self.core.db.commit()
        self.core.audit_service.record(
            AuditEvent.create(
                action="COMPANY_EVIDENCE_CREATED",
                organisation_id=context.organisation_id,
                identity_id=context.identity_id,
                target_type="COMPLIANCE_EVIDENCE",
                target_id=evidence_id,
                request_id=context.request_id,
            )
        )
        return self.get_evidence(context, evidence_id)

    def get_evidence(self, context, evidence_id) -> ApiResponse:
        self.core_api.require_permission(context, "company.reports.view")
        row = self.core.db.execute(
            "SELECT * FROM company_compliance_evidence WHERE id = ? AND organisation_id = ?",
            (str(evidence_id), str(context.organisation_id)),
        ).fetchone()
        if row is None:
            from phoenix_core.errors import NotFoundError
            raise NotFoundError("Compliance evidence not found.")
        return ApiResponse(data=dict(row), request_id=context.request_id)
