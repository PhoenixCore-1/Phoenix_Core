"""Core Shared role and permission persistence service."""

from datetime import datetime
from uuid import UUID, uuid4

from phoenix_core.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from phoenix_core.roles.domain import Role
from phoenix_core.permissions.domain import Permission


class RoleService:
    """Authoritative persistence/application service for roles and permissions."""

    def __init__(self, db):
        self.db = db

    def create_role(
        self,
        organisation_id: UUID,
        code: str,
        name: str,
        scope: str = "ORGANISATION",
    ) -> Role:
        role = Role.create(organisation_id, code, name, scope)

        if not self.db.execute(
            "SELECT 1 FROM organisations WHERE id=?",
            (str(organisation_id),),
        ).fetchone():
            raise NotFoundError("Organisation not found.")

        try:
            self.db.execute(
                """
                INSERT INTO roles(
                    id,organisation_id,code,name,scope,status,created_at
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    str(role.id),
                    str(role.organisation_id),
                    role.code,
                    role.name,
                    role.scope,
                    role.status,
                    role.created_at.isoformat(),
                ),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError(
                    "Role code already exists for this organisation."
                ) from exc
            raise

        return role

    def assign_role(self, membership_id: UUID, role_id: UUID) -> str:
        membership = self.db.execute(
            """
            SELECT organisation_id
            FROM organisation_memberships
            WHERE id=? AND status='ACTIVE'
            """,
            (str(membership_id),),
        ).fetchone()

        if not membership:
            raise NotFoundError("Active membership not found.")

        role = self.db.execute(
            """
            SELECT organisation_id
            FROM roles
            WHERE id=? AND status='ACTIVE'
            """,
            (str(role_id),),
        ).fetchone()

        if not role:
            raise NotFoundError("Active role not found.")

        if membership["organisation_id"] != role["organisation_id"]:
            raise AuthorizationError(
                "Role and membership belong to different organisations."
            )

        assignment_id = str(uuid4())

        try:
            self.db.execute(
                """
                INSERT INTO role_assignments(
                    id,membership_id,role_id,created_at
                ) VALUES (?,?,?,datetime('now'))
                """,
                (assignment_id, str(membership_id), str(role_id)),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError("Role is already assigned.") from exc
            raise

        return assignment_id

    def get_role(self, role_id: UUID) -> Role:
        row = self.db.execute(
            """
            SELECT id,organisation_id,code,name,scope,status,created_at
            FROM roles
            WHERE id=?
            """,
            (str(role_id),),
        ).fetchone()

        if not row:
            raise NotFoundError("Role not found.")

        return Role(
            UUID(row["id"]),
            UUID(row["organisation_id"]),
            row["code"],
            row["name"],
            row["scope"],
            row["status"],
            datetime.fromisoformat(row["created_at"]),
        )

    def update_role(
        self,
        role_id: UUID,
        *,
        code: str | None = None,
        name: str | None = None,
    ) -> Role:
        current = self.get_role(role_id)
        updated = current.with_details(code=code, name=name)

        try:
            self.db.execute(
                "UPDATE roles SET code=?,name=? WHERE id=?",
                (updated.code, updated.name, str(role_id)),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError(
                    "Role code already exists for this organisation."
                ) from exc
            raise

        return updated

    def set_role_status(self, role_id: UUID, status: str) -> Role:
        current = self.get_role(role_id)
        updated = current.with_status(status)

        if updated.status == current.status:
            return current

        self.db.execute(
            "UPDATE roles SET status=? WHERE id=?",
            (updated.status, str(role_id)),
        )
        self.db.commit()

        return updated

    def create_permission(self, code: str, name: str) -> Permission:
        permission = Permission.create(code, name)

        try:
            self.db.execute(
                """
                INSERT INTO permissions(
                    id,code,name,created_at
                ) VALUES (?,?,?,?)
                """,
                (
                    str(permission.id),
                    permission.code,
                    permission.name,
                    permission.created_at.isoformat(),
                ),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError(
                    "Permission code already exists."
                ) from exc
            raise

        return permission

    def get_permission(self, permission_id: UUID) -> Permission:
        row = self.db.execute(
            """
            SELECT id,code,name,created_at
            FROM permissions
            WHERE id=?
            """,
            (str(permission_id),),
        ).fetchone()

        if not row:
            raise NotFoundError("Permission not found.")

        return Permission(
            UUID(row["id"]),
            row["code"],
            row["name"],
            datetime.fromisoformat(row["created_at"]),
        )

    def get_permission_by_code(self, code: str) -> Permission:
        code = code.strip().lower()

        row = self.db.execute(
            """
            SELECT id,code,name,created_at
            FROM permissions
            WHERE code=?
            """,
            (code,),
        ).fetchone()

        if not row:
            raise NotFoundError("Permission not found.")

        return Permission(
            UUID(row["id"]),
            row["code"],
            row["name"],
            datetime.fromisoformat(row["created_at"]),
        )
    def grant_permission(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        role = self.get_role(role_id)
        permission = self.get_permission(permission_id)

        if role.status != "ACTIVE":
            raise AuthorizationError(
                "Permissions can only be assigned to an active role."
            )

        try:
            self.db.execute(
                """
                INSERT INTO role_permissions(
                    role_id,permission_id,created_at
                ) VALUES (?,?,datetime('now'))
                """,
                (str(role.id), str(permission.id)),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError(
                    "Permission is already granted to this role."
                ) from exc
            raise

    def revoke_permission(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> bool:
        self.get_role(role_id)
        self.get_permission(permission_id)

        cur = self.db.execute(
            """
            DELETE FROM role_permissions
            WHERE role_id=? AND permission_id=?
            """,
            (str(role_id), str(permission_id)),
        )
        self.db.commit()

        return cur.rowcount == 1

    def remove_role(
        self,
        membership_id: UUID,
        role_id: UUID,
    ) -> bool:
        self.get_role(role_id)

        cur = self.db.execute(
            """
            DELETE FROM role_assignments
            WHERE membership_id=? AND role_id=?
            """,
            (str(membership_id), str(role_id)),
        )
        self.db.commit()

        return cur.rowcount == 1

