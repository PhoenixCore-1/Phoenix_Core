from uuid import UUID

from phoenix_core.errors import AuthorizationError, ConflictError, NotFoundError
from phoenix_core.organisations.domain import Organisation
from phoenix_core.organisations.membership import Membership


class CompanyMembershipApplicationService:
    """Company Platform application service for organisation memberships."""

    def __init__(self, core_api):
        self.core_api = core_api
        self.db = core_api.db

    def get_membership(self, membership_id: UUID) -> Membership:
        row = self.db.execute(
            "SELECT id,identity_id,organisation_id,status,created_at "
            "FROM organisation_memberships WHERE id=?",
            (str(membership_id),),
        ).fetchone()
        if not row:
            raise NotFoundError("Membership not found.")

        from datetime import datetime

        return Membership(
            UUID(row["id"]),
            UUID(row["identity_id"]),
            UUID(row["organisation_id"]),
            row["status"],
            datetime.fromisoformat(row["created_at"]),
        )

    def list_memberships(
        self,
        organisation_id: UUID,
        *,
        status: str | None = None,
    ) -> list[Membership]:
        if not self.db.execute(
            "SELECT 1 FROM organisations WHERE id=?",
            (str(organisation_id),),
        ).fetchone():
            raise NotFoundError("Organisation not found.")

        sql = (
            "SELECT id,identity_id,organisation_id,status,created_at "
            "FROM organisation_memberships WHERE organisation_id=?"
        )
        params: list[str] = [str(organisation_id)]

        if status is not None:
            if status not in {"ACTIVE", "SUSPENDED", "REMOVED"}:
                from phoenix_core.errors import ValidationError
                raise ValidationError("Invalid membership status.")
            sql += " AND status=?"
            params.append(status)

        sql += " ORDER BY created_at, id"

        rows = self.db.execute(sql, params).fetchall()

        from datetime import datetime

        return [
            Membership(
                UUID(row["id"]),
                UUID(row["identity_id"]),
                UUID(row["organisation_id"]),
                row["status"],
                datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def set_membership_status(
        self,
        membership_id: UUID,
        status: str,
    ) -> Membership:
        current = self.get_membership(membership_id)
        updated = current.with_status(status)

        if updated.status == current.status:
            return current

        if status == "ACTIVE":
            org = self.db.execute(
                "SELECT status FROM organisations WHERE id=?",
                (str(current.organisation_id),),
            ).fetchone()

            if not org:
                raise NotFoundError("Organisation not found.")

            if org["status"] != "ACTIVE":
                raise AuthorizationError(
                    "Membership cannot be activated while the organisation is not active."
                )

            identity = self.db.execute(
                "SELECT status FROM identities WHERE id=?",
                (str(current.identity_id),),
            ).fetchone()

            if not identity or identity["status"] != "ACTIVE":
                raise AuthorizationError(
                    "Membership cannot be activated for an inactive identity."
                )

        self.db.execute(
            "UPDATE organisation_memberships SET status=? WHERE id=?",
            (status, str(membership_id)),
        )
        self.db.commit()

        return updated

    def suspend_membership(self, membership_id: UUID) -> Membership:
        return self.set_membership_status(membership_id, "SUSPENDED")

    def remove_membership(self, membership_id: UUID) -> Membership:
        return self.set_membership_status(membership_id, "REMOVED")

    def restore_membership(self, membership_id: UUID) -> Membership:
        return self.set_membership_status(membership_id, "ACTIVE")

    def add_membership(
        self,
        identity_id: UUID,
        organisation_id: UUID,
    ) -> Membership:
        membership = Membership.create(identity_id, organisation_id)

        try:
            if not self.db.execute(
                "SELECT 1 FROM identities WHERE id=?",
                (str(identity_id),),
            ).fetchone():
                raise NotFoundError("Identity not found.")

            org_row = self.db.execute(
                "SELECT status FROM organisations WHERE id=?",
                (str(organisation_id),),
            ).fetchone()

            if not org_row:
                raise NotFoundError("Organisation not found.")

            if org_row["status"] != "ACTIVE":
                raise AuthorizationError(
                    "Membership can only be added to an active organisation."
                )

            self.db.execute(
                "INSERT INTO organisation_memberships"
                "(id,identity_id,organisation_id,status,created_at) "
                "VALUES (?,?,?,?,?)",
                (
                    str(membership.id),
                    str(identity_id),
                    str(organisation_id),
                    membership.status,
                    membership.created_at.isoformat(),
                ),
            )
            self.db.commit()

        except Exception as exc:
            self.db.rollback()

            if isinstance(exc, NotFoundError):
                raise

            if "UNIQUE" in str(exc).upper():
                raise ConflictError("Membership already exists.") from exc

            raise

        return membership

