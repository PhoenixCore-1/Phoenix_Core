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
from phoenix_core.organisations.membership import Membership


class RoleService:
    """Authoritative persistence/application service for roles and permissions."""

    _PROTECTED_ROLE_CODES = frozenset({
        "COMPANY.ADMIN",
    })

    def __init__(self, db):
        self.db = db

    def _ensure_role_mutable(self, role_id: UUID) -> Role:
        role = self.get_role(role_id)

        if role.code in self._PROTECTED_ROLE_CODES:
            raise AuthorizationError(
                "Protected system role cannot be modified."
            )

        return role

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

    def _ensure_role_assignable(self, role_id: UUID) -> Role:
        role = self.get_role(role_id)

        if role.code in self._PROTECTED_ROLE_CODES:
            raise AuthorizationError(
                "Protected system role cannot be assigned through company role management."
            )

        return role

    def get_membership(self, membership_id: UUID) -> Membership:
        row = self.db.execute(
            """
            SELECT id,identity_id,organisation_id,status,created_at
            FROM organisation_memberships
            WHERE id=?
            """,
            (str(membership_id),),
        ).fetchone()

        if not row:
            raise NotFoundError("Membership not found.")

        return Membership(
            UUID(row["id"]),
            UUID(row["identity_id"]),
            UUID(row["organisation_id"]),
            row["status"],
            datetime.fromisoformat(row["created_at"]),
        )

    def list_assigned_roles(self, membership_id: UUID) -> list[Role]:
        rows = self.db.execute(
            "SELECT id,organisation_id,code,name,scope,status,created_at FROM roles WHERE id IN (SELECT role_id FROM role_assignments WHERE membership_id=?) ORDER BY name",
            (str(membership_id),),
        ).fetchall()

        return [
            Role(
                UUID(row["id"]),
                UUID(row["organisation_id"]),
                row["code"],
                row["name"],
                row["scope"],
                row["status"],
                datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

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

        self._ensure_role_assignable(role_id)

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

    def list_roles(
        self,
        organisation_id: UUID,
        *,
        status: str | None = None,
    ) -> list[Role]:
        sql = """
            SELECT id,organisation_id,code,name,scope,status,created_at
            FROM roles
            WHERE organisation_id=?
        """
        params: list[str] = [str(organisation_id)]

        if status is not None:
            if status not in {"ACTIVE", "DISABLED"}:
                raise ValidationError("Invalid role status.")
            sql += " AND status=?"
            params.append(status)

        sql += " ORDER BY code"

        rows = self.db.execute(sql, params).fetchall()

        return [
            Role(
                UUID(row["id"]),
                UUID(row["organisation_id"]),
                row["code"],
                row["name"],
                row["scope"],
                row["status"],
                datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]
    def update_role(
        self,
        role_id: UUID,
        *,
        code: str | None = None,
        name: str | None = None,
    ) -> Role:
        current = self._ensure_role_mutable(role_id)
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
        current = self._ensure_role_mutable(role_id)
        updated = current.with_status(status)

        if updated.status == current.status:
            return current

        self.db.execute(
            "UPDATE roles SET status=? WHERE id=?",
            (updated.status, str(role_id)),
        )
        self.db.commit()

        return updated

    def disable_role(self, role_id: UUID) -> Role:
        return self.set_role_status(role_id, "DISABLED")

    def enable_role(self, role_id: UUID) -> Role:
        return self.set_role_status(role_id, "ACTIVE")
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
    def list_permissions(self) -> list[Permission]:
        rows = self.db.execute(
            """
            SELECT id,code,name,created_at
            FROM permissions
            ORDER BY code
            """
        ).fetchall()

        return [
            Permission(
                UUID(row["id"]),
                row["code"],
                row["name"],
                datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def update_permission(
        self,
        permission_id: UUID,
        *,
        code: str | None = None,
        name: str | None = None,
    ) -> Permission:
        current = self.get_permission(permission_id)
        updated = current.with_details(code=code, name=name)

        try:
            self.db.execute(
                "UPDATE permissions SET code=?,name=? WHERE id=?",
                (
                    updated.code,
                    updated.name,
                    str(permission_id),
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

        return updated
    def assign_protected_company_admin(
        self,
        membership_id: UUID,
        role_id: UUID,
    ) -> str:
        """Assign the protected COMPANY.ADMIN role during system provisioning."""

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
            SELECT organisation_id, code, scope
            FROM roles
            WHERE id=? AND status='ACTIVE'
            """,
            (str(role_id),),
        ).fetchone()

        if not role:
            raise NotFoundError("Active role not found.")

        if role["code"] != "COMPANY.ADMIN":
            raise AuthorizationError(
                "Only COMPANY.ADMIN can be assigned through system provisioning."
            )

        if role["scope"] != "ORGANISATION":
            raise AuthorizationError(
                "COMPANY.ADMIN must be an organisation-scoped role."
            )

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
                (
                    assignment_id,
                    str(membership_id),
                    str(role_id),
                ),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()

            if "UNIQUE" in str(exc).upper():
                raise ConflictError(
                    "Role is already assigned."
                ) from exc

            raise

        return assignment_id
    def grant_permission(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        role = self._ensure_role_mutable(role_id)
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
        self._ensure_role_mutable(role_id)
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

    def list_role_permissions(
        self,
        role_id: UUID,
    ) -> list[Permission]:
        self.get_role(role_id)

        rows = self.db.execute(
            """
            SELECT p.id,p.code,p.name,p.created_at
            FROM role_permissions rp
            JOIN permissions p ON p.id=rp.permission_id
            WHERE rp.role_id=?
            ORDER BY p.code
            """,
            (str(role_id),),
        ).fetchall()

        return [
            Permission(
                UUID(row["id"]),
                row["code"],
                row["name"],
                datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]
    def remove_role(
        self,
        membership_id: UUID,
        role_id: UUID,
    ) -> bool:
        self._ensure_role_assignable(role_id)

        cur = self.db.execute(
            """
            DELETE FROM role_assignments
            WHERE membership_id=? AND role_id=?
            """,
            (str(membership_id), str(role_id)),
        )
        self.db.commit()

        return cur.rowcount == 1




