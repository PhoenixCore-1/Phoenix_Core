"""Tenant-scoped compliance expiry monitoring.

Monitoring is a read-only projection over authoritative Core legal/evidence
records. It never changes evidence or legal records automatically.
"""

from datetime import datetime, timezone

from phoenix_core.api.contracts import ApiResponse


class CompanyComplianceMonitoringService:
    """Calculate expiry state for company compliance evidence."""

    def __init__(self, core_api):
        self.core_api = core_api
        self.core = core_api.core_service

    @staticmethod
    def _parse(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
        except (TypeError, ValueError):
            return None

    def overview(self, context, *, days: int = 30) -> ApiResponse:
        self.core_api.require_permission(context, "company.reports.view")
        days = max(1, min(int(days), 365))
        now = datetime.now(timezone.utc)
        cutoff = now.timestamp() + days * 86400

        rows = self.core.db.execute(
            """
            SELECT id, title, evidence_type, status, valid_from, valid_until,
                   policy_version_id, document_id, document_version_id, created_at
            FROM company_compliance_evidence
            WHERE organisation_id = ?
              AND status != 'ARCHIVED'
            ORDER BY valid_until IS NULL, valid_until, created_at DESC
            """,
            (str(context.organisation_id),),
        ).fetchall()

        items = []
        counts = {"CURRENT": 0, "EXPIRING_SOON": 0, "EXPIRED": 0, "NO_EXPIRY": 0}
        for row in rows:
            expiry = self._parse(row["valid_until"])
            if expiry is None:
                state = "NO_EXPIRY"
                counts[state] += 1
                days_remaining = None
            else:
                days_remaining = int((expiry - now).total_seconds() // 86400)
                if expiry <= now:
                    state = "EXPIRED"
                elif expiry.timestamp() <= cutoff:
                    state = "EXPIRING_SOON"
                else:
                    state = "CURRENT"
                counts[state] += 1

            items.append({
                "id": row["id"],
                "title": row["title"],
                "evidence_type": row["evidence_type"],
                "record_status": row["status"],
                "valid_from": row["valid_from"],
                "valid_until": row["valid_until"],
                "days_remaining": days_remaining,
                "state": state,
                "policy_version_id": row["policy_version_id"],
                "document_id": row["document_id"],
                "document_version_id": row["document_version_id"],
            })

        return ApiResponse(
            data={
                "organisation_id": str(context.organisation_id),
                "scope": "COMPANY_COMPLIANCE_MONITORING",
                "authority": "PHOENIX_CORE",
                "window_days": days,
                "evaluated_at": now.isoformat(),
                "summary": counts,
                "action_required": counts["EXPIRED"] + counts["EXPIRING_SOON"],
                "items": items,
                "mutations_performed": False,
            },
            request_id=context.request_id,
        )
