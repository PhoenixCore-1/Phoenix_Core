"""Phoenix Core API request-context resolution."""

from uuid import UUID

from phoenix_core.errors import AuthenticationError
from phoenix_core.authorization.service import AuthorizationService
from phoenix_core.security.context import RequestContext
from phoenix_core.sessions.service import SessionService


class RequestContextResolver:
    """Resolve an authenticated API request into authoritative Core context."""

    def __init__(self, db, core_service):
        self.db = db
        self.core_service = core_service
        self.authorization_service = AuthorizationService(db)
        self.session_service = SessionService(db)

    def resolve(
        self,
        *,
        request_id: str,
        session_id: UUID,
        organisation_id: UUID | None = None,
    ) -> RequestContext:
        session = self.session_service.get_active(session_id)
        identity_id = UUID(session["identity_id"])

        user = self.db.execute(
            """
            SELECT platform_level
            FROM users
            WHERE identity_id=?
            """,
            (str(identity_id),),
        ).fetchone()

        platform_level = user["platform_level"] if user else None

        # System Admin operates above the company/tenant level.
        if platform_level == "SYSTEM_ADMIN":
            return RequestContext(
                request_id=request_id,
                identity_id=identity_id,
                organisation_id=None,
                session_id=session_id,
                permissions=frozenset(),
                entitlements=frozenset(),
            )

        # Company users must always operate inside an organisation.
        if organisation_id is None:
            raise AuthenticationError(
                "An organisation context is required for authenticated API access."
            )

        membership = self.db.execute(
            """
            SELECT 1
            FROM organisation_memberships m
            JOIN organisations o ON o.id = m.organisation_id
            WHERE m.identity_id=?
              AND m.organisation_id=?
              AND m.status='ACTIVE'
              AND o.status='ACTIVE'
            """,
            (str(identity_id), str(organisation_id)),
        ).fetchone()

        if not membership:
            raise AuthenticationError(
                "User is not an active member of this organisation."
            )

        permissions = self.authorization_service.effective_permissions(
            identity_id,
            organisation_id,
        )

        entitlements = {
            row["code"]
            for row in self.db.execute(
                """
                SELECT DISTINCT m.code
                FROM module_entitlements me
                JOIN modules m ON m.id = me.module_id
                WHERE me.organisation_id=?
                  AND me.status='ACTIVE'
                  AND m.status='ENABLED'
                ORDER BY m.code
                """,
                (str(organisation_id),),
            ).fetchall()
        }

        return RequestContext(
            request_id=request_id,
            identity_id=identity_id,
            organisation_id=organisation_id,
            session_id=session_id,
            permissions=frozenset(permissions),
            entitlements=frozenset(entitlements),
        )
