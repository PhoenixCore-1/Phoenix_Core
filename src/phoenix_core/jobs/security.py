"""Phoenix Core background-job security boundary."""

from uuid import UUID

from phoenix_core.errors import AuthenticationError, AuthorizationError
from phoenix_core.jobs.domain import Job
from phoenix_core.security.context import RequestContext


class JobSecurityService:
    """Validate background-job execution against current Core authority."""

    def __init__(self, db, core_service):
        self.db = db
        self.core_service = core_service

    def validate_execution(
        self,
        job: Job,
        context: RequestContext | None = None,
        *,
        required_permission: str | None = None,
        required_entitlement: str | None = None,
    ) -> None:
        """Validate that a job is currently authorised to execute."""

        if job.organisation_id is None and job.identity_id is None:
            if context is not None:
                raise AuthorizationError(
                    "A system job cannot execute with a user context."
                )

            return

        if job.organisation_id is None or job.identity_id is None:
            raise AuthorizationError(
                "Tenant-bound jobs must contain both organisation and identity context."
            )

        organisation_id = job.organisation_id
        identity_id = job.identity_id

        organisation = self.core_service.get_organisation(organisation_id)

        if organisation.status != "ACTIVE":
            raise AuthorizationError(
                "Job organisation is not active."
            )

        identity = self.core_service.get_identity(identity_id)

        if identity.status != "ACTIVE":
            raise AuthorizationError(
                "Job identity is not active."
            )

        membership = self.db.execute(
            """
            SELECT id
            FROM organisation_memberships
            WHERE identity_id=?
              AND organisation_id=?
              AND status='ACTIVE'
            """,
            (
                str(identity_id),
                str(organisation_id),
            ),
        ).fetchone()

        if membership is None:
            raise AuthorizationError(
                "Job identity is not an active member of the job organisation."
            )

        if context is not None:
            if context.organisation_id != organisation_id:
                raise AuthorizationError(
                    "Job organisation does not match execution context."
                )

            if context.identity_id != identity_id:
                raise AuthorizationError(
                    "Job identity does not match execution context."
                )

        if required_permission is not None:
            permissions = self.core_service.effective_permissions(
                identity_id,
                organisation_id,
            )

            if required_permission not in permissions:
                raise AuthorizationError(
                    "Job execution permission denied."
                )

        if required_entitlement is not None:
            module = self.core_service.get_module_by_code(
                required_entitlement
            )

            if not self.core_service.module_available(
                organisation_id,
                module.id,
            ):
                raise AuthorizationError(
                    "Job module entitlement is not active."
                )
