"""Company Platform compliance and legal oversight.

This service is deliberately read-only in its first slice. It exposes the
existing Core policy/version/acceptance authority to the tenant Company
Platform without creating a second legal or evidence store.
"""

from phoenix_core.api.contracts import ApiResponse


class CompanyComplianceApplicationService:
    """Expose tenant-scoped compliance status from Core legal records."""

    def __init__(self, core_api):
        self.core_api = core_api
        self.core = core_api.core_service

    def overview(self, context) -> ApiResponse:
        self.core_api.require_permission(context, "company.reports.view")
        rows = self.core.db.execute(
            """
            SELECT
                p.id AS policy_id,
                p.policy_code,
                p.policy_type,
                p.status AS policy_status,
                p.required_acceptance,
                pv.id AS version_id,
                pv.version_number,
                pv.version_label,
                pv.document_id,
                pv.effective_at,
                pv.acceptance_required,
                pv.status AS version_status,
                (
                    SELECT COUNT(*)
                    FROM policy_acceptances pa
                    WHERE pa.organisation_id = p.organisation_id
                      AND pa.policy_version_id = pv.id
                ) AS acceptance_count,
                EXISTS (
                    SELECT 1
                    FROM policy_acceptances pa2
                    WHERE pa2.organisation_id = p.organisation_id
                      AND pa2.policy_version_id = pv.id
                      AND pa2.identity_id = ?
                ) AS current_identity_accepted
            FROM policies p
            JOIN policy_versions pv ON pv.policy_id = p.id
            WHERE p.organisation_id = ?
              AND p.status = 'ACTIVE'
              AND pv.status = 'ACTIVE'
            ORDER BY p.policy_code, pv.version_number DESC
            """,
            (str(context.identity_id), str(context.organisation_id)),
        ).fetchall()

        items = []
        for row in rows:
            items.append({
                "policy_id": row["policy_id"],
                "policy_code": row["policy_code"],
                "policy_type": row["policy_type"],
                "policy_status": row["policy_status"],
                "required_acceptance": bool(row["required_acceptance"]),
                "version": {
                    "id": row["version_id"],
                    "number": row["version_number"],
                    "label": row["version_label"],
                    "document_id": row["document_id"],
                    "effective_at": row["effective_at"],
                    "status": row["version_status"],
                },
                "acceptance_required": bool(row["acceptance_required"]),
                "acceptance_count": row["acceptance_count"],
                "current_identity_accepted": bool(row["current_identity_accepted"]),
                "status": "ACCEPTED" if row["current_identity_accepted"] else (
                    "ACTION_REQUIRED" if row["acceptance_required"] else "INFORMATIONAL"
                ),
            })

        required = [item for item in items if item["acceptance_required"]]
        accepted = [item for item in required if item["current_identity_accepted"]]
        return ApiResponse(
            data={
                "organisation_id": str(context.organisation_id),
                "scope": "COMPANY_COMPLIANCE",
                "authority": "PHOENIX_CORE",
                "summary": {
                    "active_requirements": len(required),
                    "current_identity_accepted": len(accepted),
                    "action_required": len(required) - len(accepted),
                    "status": "COMPLIANT" if len(required) == len(accepted) else "ACTION_REQUIRED",
                },
                "items": items,
                "capabilities": {
                    "requirements": True,
                    "policy_versions": True,
                    "acceptance_status": True,
                    "contracts": False,
                    "evidence_records": False,
                },
            },
            request_id=context.request_id,
        )
