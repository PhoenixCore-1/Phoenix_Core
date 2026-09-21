from uuid import UUID

from phoenix_core.errors import ConflictError, NotFoundError, ValidationError
from phoenix_core.identity.domain import Identity
from phoenix_core.security.passwords import hash_password
from phoenix_core.users.domain import User


class UserApplicationService:
    """User Platform application service."""

    def __init__(self, core_api):
        self.core_api = core_api
        self.db = core_api.db

    def create_user(
        self,
        *,
        username: str,
        display_name: str,
        password: str,
    ) -> User:
        identity = Identity.create("HUMAN")
        user = User.create(
            identity.id,
            username,
            display_name,
            hash_password(password),
        )

        try:
            self.db.execute(
                "INSERT INTO identities(id,identity_type,status,created_at) "
                "VALUES (?,?,?,?)",
                (
                    str(identity.id),
                    identity.identity_type,
                    identity.status,
                    identity.created_at.isoformat(),
                ),
            )
            self.db.execute(
                "INSERT INTO users("
                "id,identity_id,username,display_name,password_hash,status,created_at"
                ") VALUES (?,?,?,?,?,?,?)",
                (
                    str(user.id),
                    str(user.identity_id),
                    user.username,
                    user.display_name,
                    user.password_hash,
                    user.status,
                    user.created_at.isoformat(),
                ),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError("Username already exists.") from exc
            raise

        return user

    def get_user(self, user_id: UUID) -> User:
        row = self.db.execute(
            "SELECT id,identity_id,username,display_name,password_hash,status,created_at "
            "FROM users WHERE id=?",
            (str(user_id),),
        ).fetchone()

        if not row:
            raise NotFoundError("User not found.")

        from datetime import datetime

        return User(
            UUID(row["id"]),
            UUID(row["identity_id"]),
            row["username"],
            row["display_name"],
            row["password_hash"],
            row["status"],
            datetime.fromisoformat(row["created_at"]),
        )

    def get_user_by_identity(self, identity_id: UUID) -> User:
        row = self.db.execute(
            "SELECT id,identity_id,username,display_name,password_hash,status,created_at "
            "FROM users WHERE identity_id=?",
            (str(identity_id),),
        ).fetchone()

        if not row:
            raise NotFoundError("User not found.")

        from datetime import datetime

        return User(
            UUID(row["id"]),
            UUID(row["identity_id"]),
            row["username"],
            row["display_name"],
            row["password_hash"],
            row["status"],
            datetime.fromisoformat(row["created_at"]),
        )

    def update_user(
        self,
        user_id: UUID,
        *,
        username: str | None = None,
        display_name: str | None = None,
    ) -> User:
        current = self.get_user(user_id)

        new_username = (
            current.username if username is None else username.strip()
        )
        new_display_name = (
            current.display_name
            if display_name is None
            else display_name.strip()
        )

        if not new_username:
            raise ValidationError("Username is required.")
        if not new_display_name:
            raise ValidationError("Display name is required.")

        try:
            self.db.execute(
                "UPDATE users SET username=?,display_name=? WHERE id=?",
                (
                    new_username,
                    new_display_name,
                    str(user_id),
                ),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError("Username already exists.") from exc
            raise

        return self.get_user(user_id)

    def suspend_user(self, user_id: UUID) -> None:
        self._set_user_status(user_id, "SUSPENDED")

    def reactivate_user(self, user_id: UUID) -> None:
        self._set_user_status(user_id, "ACTIVE")

    def deactivate_user(self, user_id: UUID) -> None:
        self._set_user_status(user_id, "DISABLED")

    def _set_user_status(self, user_id: UUID, status: str) -> None:
        current = self.get_user(user_id)

        if current.status == status:
            return

        self.db.execute(
            "UPDATE users SET status=? WHERE id=?",
            (status, str(user_id)),
        )
        self.db.execute(
            "UPDATE identities SET status=? WHERE id=?",
            (status, str(current.identity_id)),
        )

        if status != "ACTIVE":
            self.db.execute(
                "UPDATE sessions SET status='REVOKED' "
                "WHERE identity_id=? AND status='ACTIVE'",
                (str(current.identity_id),),
            )

        self.db.commit()

