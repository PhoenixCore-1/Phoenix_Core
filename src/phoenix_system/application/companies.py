from datetime import datetime
from uuid import UUID

from phoenix_core.errors import ConflictError, NotFoundError, ValidationError
from phoenix_core.organisations.domain import Organisation


class SystemCompanyApplicationService:
    """System Platform application service for company lifecycle."""

    def __init__(self, core_api):
        self.core_api = core_api
        self.db = core_api.db

    def create_company(self, code: str, name: str) -> Organisation:
        org = Organisation.create(code, name)

        try:
            self.db.execute(
                "INSERT INTO organisations(id,code,name,status,created_at) "
                "VALUES (?,?,?,?,?)",
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

    def get_company(self, organisation_id: UUID) -> Organisation:
        row = self.db.execute(
            "SELECT id,code,name,status,created_at "
            "FROM organisations WHERE id=?",
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

    def update_company(
        self,
        organisation_id: UUID,
        *,
        code: str | None = None,
        name: str | None = None,
    ) -> Organisation:
        current = self.get_company(organisation_id)

        new_code = current.code if code is None else code.strip().upper()
        new_name = current.name if name is None else name.strip()

        if not new_code:
            raise ValidationError("Organisation code is required.")

        if not new_name:
            raise ValidationError("Organisation name is required.")

        try:
            self.db.execute(
                "UPDATE organisations SET code=?,name=? WHERE id=?",
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

        return self.get_company(organisation_id)

    def _set_company_status(
        self,
        organisation_id: UUID,
        status: str,
    ) -> Organisation:
        current = self.get_company(organisation_id)

        if current.status == status:
            return current

        self.db.execute(
            "UPDATE organisations SET status=? WHERE id=?",
            (status, str(organisation_id)),
        )
        self.db.commit()

        return self.get_company(organisation_id)

    def suspend_company(self, organisation_id: UUID) -> Organisation:
        return self._set_company_status(
            organisation_id,
            "SUSPENDED",
        )

    def activate_company(self, organisation_id: UUID) -> Organisation:
        return self._set_company_status(
            organisation_id,
            "ACTIVE",
        )

    def close_company(self, organisation_id: UUID) -> Organisation:
        return self._set_company_status(
            organisation_id,
            "CLOSED",
        )
