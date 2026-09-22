from uuid import UUID


class AuthorizationService:
    """Core Shared authorization and effective-permission resolution."""

    def __init__(self, db, entitlement_service):
        self.db = db
        self.entitlement_service = entitlement_service

    def effective_permissions(
        self,
        identity_id: UUID,
        organisation_id: UUID,
    ) -> set[str]:
        rows = self.db.execute(
            """
            SELECT DISTINCT p.code
            FROM organisation_memberships m
            JOIN organisations o ON o.id = m.organisation_id
            JOIN role_assignments ra ON ra.membership_id = m.id
            JOIN roles r ON r.id = ra.role_id
            JOIN role_permissions rp ON rp.role_id = r.id
            JOIN permissions p ON p.id = rp.permission_id
            WHERE m.identity_id=? AND m.organisation_id=?
              AND m.status='ACTIVE'
              AND o.status='ACTIVE'
              AND r.status='ACTIVE'
            """,
            (str(identity_id), str(organisation_id)),
        ).fetchall()

        return {row["code"] for row in rows}

    def has_capability(
        self,
        identity_id: UUID,
        organisation_id: UUID,
        permission: str,
        module_id: UUID,
    ) -> bool:
        if not self.entitlement_service.is_module_available(
            organisation_id,
            module_id,
        ):
            return False

        return self.authorize(
            identity_id,
            organisation_id,
            permission,
        )

    def authorize(
        self,
        identity_id: UUID,
        organisation_id: UUID,
        permission: str,
    ) -> bool:
        return permission in self.effective_permissions(
            identity_id,
            organisation_id,
        )