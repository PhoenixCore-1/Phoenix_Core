from datetime import datetime
from uuid import UUID

from phoenix_core.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from phoenix_core.organisations.domain import Organisation


class OrganisationService:
    """Core Shared organisation application and persistence service."""

    def __init__(self, db):
        self.db = db

    def create_organisation(
        self,
        code: str,
        name: str,
    ) -> Organisation:
        org = Organisation.create(code, name)

        try:
            self.db.execute(
                """
                INSERT INTO organisations(
                    id,code,name,status,created_at
                ) VALUES (?,?,?,?,?)
                """,
                (
                    str(org.id),
                    org.code,
                    org.name,
                    org.status,
                    org.created_at.isoformat(),
                ),
            )
            self.db.commit()

        except Exception as exc:
            self.db.rollback()

            if "UNIQUE" in str(exc).upper():
                raise ConflictError(
                    "Organisation code or name already exists."
                ) from exc

            raise

        return org

    def get_organisation(
        self,
        organisation_id: UUID,
    ) -> Organisation:
        row = self.db.execute(
            """
            SELECT id,code,name,status,created_at
            FROM organisations
            WHERE id=?
            """,
            (str(organisation_id),),
        ).fetchone()

        if not row:
            raise NotFoundError("Organisation not found.")

        return Organisation(
            UUID(row["id"]),
            row["code"],
            row["name"],
            row["status"],
            datetime.fromisoformat(row["created_at"]),
        )

    def update_organisation(
        self,
        organisation_id: UUID,
        *,
        code: str | None = None,
        name: str | None = None,
    ) -> Organisation:
        current = self.get_organisation(organisation_id)

        new_code = (
            current.code
            if code is None
            else code.strip().upper()
        )
        new_name = (
            current.name
            if name is None
            else name.strip()
        )

        if not new_code:
            raise ValidationError("Organisation code is required.")

        if not new_name:
            raise ValidationError("Organisation name is required.")

        try:
            self.db.execute(
                """
                UPDATE organisations
                SET code=?,name=?
                WHERE id=?
                """,
                (
                    new_code,
                    new_name,
                    str(organisation_id),
                ),
            )
            self.db.commit()

        except Exception as exc:
            self.db.rollback()

            if "UNIQUE" in str(exc).upper():
                raise ConflictError(
                    "Organisation code or name already exists."
                ) from exc

            raise

        return self.get_organisation(organisation_id)

    def _set_organisation_status(
        self,
        organisation_id: UUID,
        status: str,
    ) -> Organisation:
        current = self.get_organisation(organisation_id)
        updated = current.with_status(status)

        if updated.status == current.status:
            return current

        self.db.execute(
            """
            UPDATE organisations
            SET status=?
            WHERE id=?
            """,
            (
                updated.status,
                str(organisation_id),
            ),
        )

        if updated.status in {"SUSPENDED", "CLOSED"}:
            self.db.execute(
                """
                UPDATE organisation_memberships
                SET status='SUSPENDED'
                WHERE organisation_id=?
                  AND status='ACTIVE'
                """,
                (str(organisation_id),),
            )

        self.db.commit()

        return updated

    def suspend_organisation(
        self,
        organisation_id: UUID,
    ) -> Organisation:
        return self._set_organisation_status(
            organisation_id,
            "SUSPENDED",
        )

    def activate_organisation(
        self,
        organisation_id: UUID,
    ) -> Organisation:
        return self._set_organisation_status(
            organisation_id,
            "ACTIVE",
        )

    def close_organisation(
        self,
        organisation_id: UUID,
    ) -> Organisation:
        return self._set_organisation_status(
            organisation_id,
            "CLOSED",
        )
