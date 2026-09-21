from datetime import datetime
from uuid import UUID

from phoenix_core.errors import NotFoundError
from phoenix_core.organisations.domain import Organisation


class OrganisationService:
    """Core Shared organisation lookup authority."""

    def __init__(self, db):
        self.db = db

    def get_organisation(self, organisation_id: UUID) -> Organisation:
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
