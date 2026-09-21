from datetime import datetime
from uuid import UUID

from phoenix_core.errors import NotFoundError
from phoenix_core.identity.domain import Identity


class IdentityService:
    """Core Shared identity lookup authority."""

    def __init__(self, db):
        self.db = db

    def get_identity(self, identity_id: UUID) -> Identity:
        row = self.db.execute(
            "SELECT id,identity_type,status,created_at "
            "FROM identities WHERE id=?",
            (str(identity_id),),
        ).fetchone()

        if not row:
            raise NotFoundError("Identity not found.")

        return Identity(
            UUID(row["id"]),
            row["identity_type"],
            row["status"],
            datetime.fromisoformat(row["created_at"]),
        )
