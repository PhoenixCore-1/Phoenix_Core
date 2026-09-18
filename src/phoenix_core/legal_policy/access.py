from __future__ import annotations

from uuid import UUID

from phoenix_core.legal_policy.domain import PolicyStatus


class PolicyAccessEvaluator:
    """Evaluate required legal/policy acceptance for platform access."""

    def __init__(self, legal_policy_service):
        self.service = legal_policy_service

    def required_acceptance_complete(
        self,
        organisation_id: UUID,
        identity_id: UUID,
    ) -> bool:
        rows = self.service.db.execute(
            """
            SELECT pv.id
            FROM policies p
            JOIN policy_versions pv
              ON pv.policy_id = p.id
            WHERE p.organisation_id = ?
              AND p.status = ?
              AND pv.status = ?
              AND (
                    p.required_acceptance = 1
                    OR pv.acceptance_required = 1
                  )
            ORDER BY pv.policy_id, pv.version_number DESC
            """,
            (
                str(organisation_id),
                PolicyStatus.ACTIVE.value,
                PolicyStatus.ACTIVE.value,
            ),
        ).fetchall()

        required_versions = {UUID(row["id"]) for row in rows}

        if not required_versions:
            return True

        accepted = {
            UUID(row["policy_version_id"])
            for row in self.service.db.execute(
                """
                SELECT policy_version_id
                FROM policy_acceptances
                WHERE organisation_id = ?
                  AND identity_id = ?
                """,
                (
                    str(organisation_id),
                    str(identity_id),
                ),
            ).fetchall()
        }

        return required_versions.issubset(accepted)
