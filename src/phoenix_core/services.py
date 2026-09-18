"""First Phoenix Core V2 application-service layer."""

import hashlib
import secrets
from uuid import UUID, uuid4

from phoenix_core.audit.domain import AuditEvent
from phoenix_core.audit.service import AuditService
from phoenix_core.configuration.service import ConfigurationService
from phoenix_core.communications.service import CommunicationsService
from phoenix_core.errors import AuthenticationError, AuthorizationError, ConflictError, NotFoundError, ValidationError
from phoenix_core.identity.domain import Identity
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.modules.service import ModuleService
from phoenix_core.licensing.service import EntitlementService
from phoenix_core.organisations.domain import Organisation
from phoenix_core.organisations.membership import Membership
from phoenix_core.permissions.domain import Permission
from phoenix_core.roles.domain import Role
from phoenix_core.security.passwords import hash_password, verify_password
from phoenix_core.sessions.domain import Session
from phoenix_core.users.domain import User

def _dt(value):
    return value.isoformat()

class CoreFoundationService:
    def __init__(self, db: SQLiteDatabase, *, realtime_publisher=None):
        self.db = db
        self.audit_service = AuditService(db)
        self.module_service = ModuleService(db)
        self.entitlement_service = EntitlementService(db)
        self.configuration_service = ConfigurationService(db)
        self.communications_service = CommunicationsService(
            db,
            authorize=self.authorize,
            audit_record=self.audit_service.record,
            realtime_publisher=realtime_publisher,
        )

    def initialise(self):
        schema = open(
            __import__("pathlib").Path(__file__).resolve().parents[2] / "migrations" / "001_core_foundation.sql",
            encoding="utf-8",
        ).read()
        self.db.executescript(schema)

        configuration_schema = open(
            __import__("pathlib").Path(__file__).resolve().parents[2] / "migrations" / "002_core_configuration.sql",
            encoding="utf-8",
        ).read()
        self.db.executescript(configuration_schema)

        communications_schema = open(
            __import__("pathlib").Path(__file__).resolve().parents[2] / "migrations" / "003_core_communications.sql",
            encoding="utf-8",
        ).read()
        self.db.executescript(communications_schema)

        documents_schema = open(
            __import__("pathlib").Path(__file__).resolve().parents[2] / "migrations" / "004_core_documents.sql",
            encoding="utf-8",
        ).read()
        self.db.executescript(documents_schema)

        jobs_schema = open(
            __import__("pathlib").Path(__file__).resolve().parents[2] / "migrations" / "005_core_jobs.sql",
            encoding="utf-8",
        ).read()
        self.db.executescript(jobs_schema)

        legal_policy_schema = open(
            __import__("pathlib").Path(__file__).resolve().parents[2] / "migrations" / "006_core_legal_policy_acceptance.sql",
            encoding="utf-8",
        ).read()
        self.db.executescript(legal_policy_schema)

        self.db.commit()

    def create_organisation(self, code: str, name: str) -> Organisation:
        org = Organisation.create(code, name)
        try:
            self.db.execute(
                "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
                (str(org.id), org.code, org.name, org.status, _dt(org.created_at)),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError("Organisation code or name already exists.") from exc
            raise
        return org

    def create_user(self, username: str, display_name: str, password: str) -> User:
        identity = Identity.create("HUMAN")
        user = User.create(identity.id, username, display_name, hash_password(password))
        try:
            self.db.execute(
                "INSERT INTO identities(id,identity_type,status,created_at) VALUES (?,?,?,?)",
                (str(identity.id), identity.identity_type, identity.status, _dt(identity.created_at)),
            )
            self.db.execute(
                "INSERT INTO users(id,identity_id,username,display_name,password_hash,status,created_at) VALUES (?,?,?,?,?,?,?)",
                (str(user.id), str(user.identity_id), user.username, user.display_name,
                 user.password_hash, user.status, _dt(user.created_at)),
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
            "SELECT id,identity_id,username,display_name,password_hash,status,created_at FROM users WHERE id=?",
            (str(user_id),),
        ).fetchone()
        if not row:
            raise NotFoundError("User not found.")
        from datetime import datetime
        return User(
            UUID(row["id"]), UUID(row["identity_id"]), row["username"], row["display_name"],
            row["password_hash"], row["status"], datetime.fromisoformat(row["created_at"]),
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
            UUID(row["id"]), UUID(row["identity_id"]), row["username"],
            row["display_name"], row["password_hash"], row["status"],
            datetime.fromisoformat(row["created_at"]),
        )

    def get_identity(self, identity_id: UUID) -> Identity:
        row = self.db.execute(
            "SELECT id,identity_type,status,created_at FROM identities WHERE id=?",
            (str(identity_id),),
        ).fetchone()
        if not row:
            raise NotFoundError("Identity not found.")
        from datetime import datetime
        return Identity(UUID(row["id"]), row["identity_type"], row["status"], datetime.fromisoformat(row["created_at"]))

    def update_user(self, user_id: UUID, *, username: str | None = None, display_name: str | None = None) -> User:
        current = self.get_user(user_id)
        new_username = current.username if username is None else username.strip()
        new_display_name = current.display_name if display_name is None else display_name.strip()
        if not new_username:
            raise ValidationError("Username is required.")
        if not new_display_name:
            raise ValidationError("Display name is required.")
        try:
            self.db.execute("UPDATE users SET username=?,display_name=? WHERE id=?",
                            (new_username, new_display_name, str(user_id)))
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError("Username already exists.") from exc
            raise
        return self.get_user(user_id)

    def deactivate_user(self, user_id: UUID) -> None:
        self._set_user_status(user_id, "DISABLED")

    def reactivate_user(self, user_id: UUID) -> None:
        self._set_user_status(user_id, "ACTIVE")

    def suspend_user(self, user_id: UUID) -> None:
        self._set_user_status(user_id, "SUSPENDED")

    def _set_user_status(self, user_id: UUID, status: str) -> None:
        current = self.get_user(user_id)
        if current.status == status:
            return
        self.db.execute("UPDATE users SET status=? WHERE id=?", (status, str(user_id)))
        self.db.execute("UPDATE identities SET status=? WHERE id=?", (status, str(current.identity_id)))
        if status != "ACTIVE":
            self.db.execute("UPDATE sessions SET status='REVOKED' WHERE identity_id=? AND status='ACTIVE'", (str(current.identity_id),))
        self.db.commit()

    def get_organisation(self, organisation_id: UUID) -> Organisation:
        row = self.db.execute(
            "SELECT id,code,name,status,created_at FROM organisations WHERE id=?",
            (str(organisation_id),),
        ).fetchone()
        if not row:
            raise NotFoundError("Organisation not found.")
        from datetime import datetime
        return Organisation(
            UUID(row["id"]), row["code"], row["name"], row["status"],
            datetime.fromisoformat(row["created_at"]),
        )

    def update_organisation(self, organisation_id: UUID, *, code: str | None = None, name: str | None = None) -> Organisation:
        current = self.get_organisation(organisation_id)
        new_code = current.code if code is None else code.strip().upper()
        new_name = current.name if name is None else name.strip()
        if not new_code:
            raise ValidationError("Organisation code is required.")
        if not new_name:
            raise ValidationError("Organisation name is required.")
        try:
            self.db.execute(
                "UPDATE organisations SET code=?,name=? WHERE id=?",
                (new_code, new_name, str(organisation_id)),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError("Organisation code or name already exists.") from exc
            raise
        return self.get_organisation(organisation_id)

    def _set_organisation_status(self, organisation_id: UUID, status: str) -> Organisation:
        current = self.get_organisation(organisation_id)
        updated = current.with_status(status)
        if updated.status == current.status:
            return current
        self.db.execute("UPDATE organisations SET status=? WHERE id=?", (updated.status, str(organisation_id)))
        if updated.status in {"SUSPENDED", "CLOSED"}:
            self.db.execute(
                "UPDATE organisation_memberships SET status='SUSPENDED' WHERE organisation_id=? AND status='ACTIVE'",
                (str(organisation_id),),
            )
        self.db.commit()
        return updated

    def suspend_organisation(self, organisation_id: UUID) -> Organisation:
        return self._set_organisation_status(organisation_id, "SUSPENDED")

    def activate_organisation(self, organisation_id: UUID) -> Organisation:
        return self._set_organisation_status(organisation_id, "ACTIVE")

    def close_organisation(self, organisation_id: UUID) -> Organisation:
        return self._set_organisation_status(organisation_id, "CLOSED")

    def get_membership(self, membership_id: UUID) -> Membership:
        row = self.db.execute(
            "SELECT id,identity_id,organisation_id,status,created_at FROM organisation_memberships WHERE id=?",
            (str(membership_id),),
        ).fetchone()
        if not row:
            raise NotFoundError("Membership not found.")
        from datetime import datetime
        return Membership(
            UUID(row["id"]), UUID(row["identity_id"]), UUID(row["organisation_id"]),
            row["status"], datetime.fromisoformat(row["created_at"]),
        )

    def list_memberships(self, organisation_id: UUID, *, status: str | None = None) -> list[Membership]:
        self.get_organisation(organisation_id)
        sql = "SELECT id,identity_id,organisation_id,status,created_at FROM organisation_memberships WHERE organisation_id=?"
        params: list[str] = [str(organisation_id)]
        if status is not None:
            if status not in {"ACTIVE", "SUSPENDED", "REMOVED"}:
                raise ValidationError("Invalid membership status.")
            sql += " AND status=?"
            params.append(status)
        sql += " ORDER BY created_at, id"
        rows = self.db.execute(sql, params).fetchall()
        from datetime import datetime
        return [Membership(UUID(r["id"]), UUID(r["identity_id"]), UUID(r["organisation_id"]), r["status"], datetime.fromisoformat(r["created_at"])) for r in rows]

    def set_membership_status(self, membership_id: UUID, status: str) -> Membership:
        current = self.get_membership(membership_id)
        updated = current.with_status(status)
        if updated.status == current.status:
            return current
        if status == "ACTIVE":
            org = self.get_organisation(current.organisation_id)
            if org.status != "ACTIVE":
                raise AuthorizationError("Membership cannot be activated while the organisation is not active.")
            identity = self.db.execute("SELECT status FROM identities WHERE id=?", (str(current.identity_id),)).fetchone()
            if not identity or identity["status"] != "ACTIVE":
                raise AuthorizationError("Membership cannot be activated for an inactive identity.")
        self.db.execute("UPDATE organisation_memberships SET status=? WHERE id=?", (status, str(membership_id)))
        self.db.commit()
        return updated

    def suspend_membership(self, membership_id: UUID) -> Membership:
        return self.set_membership_status(membership_id, "SUSPENDED")

    def remove_membership(self, membership_id: UUID) -> Membership:
        return self.set_membership_status(membership_id, "REMOVED")

    def restore_membership(self, membership_id: UUID) -> Membership:
        return self.set_membership_status(membership_id, "ACTIVE")

    def add_membership(self, identity_id: UUID, organisation_id: UUID) -> Membership:
        membership = Membership.create(identity_id, organisation_id)
        try:
            if not self.db.execute("SELECT 1 FROM identities WHERE id=?", (str(identity_id),)).fetchone():
                raise NotFoundError("Identity not found.")
            org_row = self.db.execute("SELECT status FROM organisations WHERE id=?", (str(organisation_id),)).fetchone()
            if not org_row:
                raise NotFoundError("Organisation not found.")
            if org_row["status"] != "ACTIVE":
                raise AuthorizationError("Membership can only be added to an active organisation.")
            self.db.execute(
                "INSERT INTO organisation_memberships(id,identity_id,organisation_id,status,created_at) VALUES (?,?,?,?,?)",
                (str(membership.id), str(identity_id), str(organisation_id), membership.status, _dt(membership.created_at)),
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

    def create_role(self, organisation_id: UUID, code: str, name: str, scope: str = "ORGANISATION") -> Role:
        role = Role.create(organisation_id, code, name, scope)
        if not self.db.execute("SELECT 1 FROM organisations WHERE id=?", (str(organisation_id),)).fetchone():
            raise NotFoundError("Organisation not found.")
        try:
            self.db.execute(
                "INSERT INTO roles(id,organisation_id,code,name,scope,status,created_at) VALUES (?,?,?,?,?,?,?)",
                (str(role.id), str(role.organisation_id), role.code, role.name, role.scope, role.status, _dt(role.created_at)),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError("Role code already exists for this organisation.") from exc
            raise
        return role

    def assign_role(self, membership_id: UUID, role_id: UUID):
        membership = self.db.execute(
            "SELECT organisation_id FROM organisation_memberships WHERE id=? AND status='ACTIVE'",
            (str(membership_id),),
        ).fetchone()
        if not membership:
            raise NotFoundError("Active membership not found.")
        role = self.db.execute(
            "SELECT organisation_id FROM roles WHERE id=? AND status='ACTIVE'",
            (str(role_id),),
        ).fetchone()
        if not role:
            raise NotFoundError("Active role not found.")
        if membership["organisation_id"] != role["organisation_id"]:
            raise AuthorizationError("Role and membership belong to different organisations.")
        assignment_id = str(uuid4())
        try:
            self.db.execute(
                "INSERT INTO role_assignments(id,membership_id,role_id,created_at) VALUES (?,?,?,datetime('now'))",
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
            "SELECT id,organisation_id,code,name,scope,status,created_at FROM roles WHERE id=?",
            (str(role_id),),
        ).fetchone()
        if not row:
            raise NotFoundError("Role not found.")
        from datetime import datetime
        return Role(UUID(row["id"]), UUID(row["organisation_id"]), row["code"], row["name"],
                    row["scope"], row["status"], datetime.fromisoformat(row["created_at"]))

    def list_roles(self, organisation_id: UUID, *, status: str | None = None) -> list[Role]:
        self.get_organisation(organisation_id)
        sql = "SELECT id,organisation_id,code,name,scope,status,created_at FROM roles WHERE organisation_id=?"
        params: list[str] = [str(organisation_id)]
        if status is not None:
            if status not in {"ACTIVE", "DISABLED"}:
                raise ValidationError("Invalid role status.")
            sql += " AND status=?"
            params.append(status)
        sql += " ORDER BY code"
        rows = self.db.execute(sql, params).fetchall()
        from datetime import datetime
        return [Role(UUID(r["id"]), UUID(r["organisation_id"]), r["code"], r["name"], r["scope"],
                     r["status"], datetime.fromisoformat(r["created_at"])) for r in rows]

    def update_role(self, role_id: UUID, *, code: str | None = None, name: str | None = None) -> Role:
        current = self.get_role(role_id)
        updated = current.with_details(code=code, name=name)
        try:
            self.db.execute("UPDATE roles SET code=?,name=? WHERE id=?",
                            (updated.code, updated.name, str(role_id)))
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError("Role code already exists for this organisation.") from exc
            raise
        return updated

    def set_role_status(self, role_id: UUID, status: str) -> Role:
        current = self.get_role(role_id)
        updated = current.with_status(status)
        if updated.status == current.status:
            return current
        self.db.execute("UPDATE roles SET status=? WHERE id=?", (updated.status, str(role_id)))
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
                "INSERT INTO permissions(id,code,name,created_at) VALUES (?,?,?,?)",
                (str(permission.id), permission.code, permission.name, _dt(permission.created_at)),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError("Permission code already exists.") from exc
            raise
        return permission

    def get_permission(self, permission_id: UUID) -> Permission:
        row = self.db.execute(
            "SELECT id,code,name,created_at FROM permissions WHERE id=?",
            (str(permission_id),),
        ).fetchone()
        if not row:
            raise NotFoundError("Permission not found.")
        from datetime import datetime
        return Permission(UUID(row["id"]), row["code"], row["name"], datetime.fromisoformat(row["created_at"]))

    def get_permission_by_code(self, code: str) -> Permission:
        code = code.strip().lower()
        row = self.db.execute(
            "SELECT id,code,name,created_at FROM permissions WHERE code=?",
            (code,),
        ).fetchone()
        if not row:
            raise NotFoundError("Permission not found.")
        from datetime import datetime
        return Permission(UUID(row["id"]), row["code"], row["name"], datetime.fromisoformat(row["created_at"]))

    def list_permissions(self) -> list[Permission]:
        rows = self.db.execute(
            "SELECT id,code,name,created_at FROM permissions ORDER BY code"
        ).fetchall()
        from datetime import datetime
        return [Permission(UUID(r["id"]), r["code"], r["name"], datetime.fromisoformat(r["created_at"])) for r in rows]

    def update_permission(self, permission_id: UUID, *, code: str | None = None, name: str | None = None) -> Permission:
        current = self.get_permission(permission_id)
        updated = current.with_details(code=code, name=name)
        try:
            self.db.execute("UPDATE permissions SET code=?,name=? WHERE id=?",
                            (updated.code, updated.name, str(permission_id)))
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError("Permission code already exists.") from exc
            raise
        return updated

    def grant_permission(self, role_id: UUID, permission_id: UUID) -> None:
        role = self.get_role(role_id)
        permission = self.get_permission(permission_id)
        if role.status != "ACTIVE":
            raise AuthorizationError("Permissions can only be assigned to an active role.")
        try:
            self.db.execute(
                "INSERT INTO role_permissions(role_id,permission_id,created_at) VALUES (?,?,datetime('now'))",
                (str(role.id), str(permission.id)),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError("Permission is already granted to this role.") from exc
            raise

    def revoke_permission(self, role_id: UUID, permission_id: UUID) -> bool:
        self.get_role(role_id)
        self.get_permission(permission_id)
        cur = self.db.execute(
            "DELETE FROM role_permissions WHERE role_id=? AND permission_id=?",
            (str(role_id), str(permission_id)),
        )
        self.db.commit()
        return cur.rowcount == 1

    def list_role_permissions(self, role_id: UUID) -> list[Permission]:
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
        from datetime import datetime
        return [Permission(UUID(r["id"]), r["code"], r["name"], datetime.fromisoformat(r["created_at"])) for r in rows]

    def list_role_assignments(self, role_id: UUID):
        self.get_role(role_id)
        rows = self.db.execute(
            """
            SELECT ra.id,ra.membership_id,ra.role_id,ra.created_at
            FROM role_assignments ra
            WHERE ra.role_id=?
            ORDER BY ra.created_at,ra.id
            """,
            (str(role_id),),
        ).fetchall()
        return rows

    def remove_role(self, membership_id: UUID, role_id: UUID) -> bool:
        self.get_role(role_id)
        self.get_membership(membership_id)
        cur = self.db.execute(
            "DELETE FROM role_assignments WHERE membership_id=? AND role_id=?",
            (str(membership_id), str(role_id)),
        )
        self.db.commit()
        return cur.rowcount == 1

    def authenticate(self, username: str, password: str, lifetime_minutes: int = 60):
        row = self.db.execute(
            "SELECT identity_id,password_hash,status FROM users WHERE username=?",
            (username.strip(),),
        ).fetchone()
        if not row or row["status"] != "ACTIVE" or not verify_password(password, row["password_hash"]):
            raise AuthenticationError("Invalid credentials.")
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        session = Session.create(UUID(row["identity_id"]), token_hash, lifetime_minutes)
        self.db.execute(
            "INSERT INTO sessions(id,identity_id,token_hash,expires_at,status,created_at) VALUES (?,?,?,?,?,?)",
            (str(session.id), str(session.identity_id), session.token_hash, _dt(session.expires_at),
             session.status, _dt(session.created_at)),
        )
        self.db.commit()
        return session, token

    def revoke_session(self, token: str):
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        cur = self.db.execute(
            "UPDATE sessions SET status='REVOKED' WHERE token_hash=? AND status='ACTIVE'",
            (token_hash,),
        )
        self.db.commit()
        return cur.rowcount == 1

    def effective_permissions(self, identity_id: UUID, organisation_id: UUID) -> set[str]:
        rows = self.db.execute(
            """
            SELECT DISTINCT p.code
            FROM organisation_memberships m
            JOIN organisations o ON o.id = m.organisation_id
            JOIN role_assignments ra ON ra.membership_id = m.id
            JOIN roles r ON r.id = ra.role_id
            JOIN role_permissions rp ON rp.role_id = r.id
            JOIN permissions p ON p.id = rp.permission_id
            WHERE m.identity_id=? AND m.organisation_id=?
              AND m.status='ACTIVE' AND o.status='ACTIVE' AND r.status='ACTIVE'
            """,
            (str(identity_id), str(organisation_id)),
        ).fetchall()
        return {row["code"] for row in rows}

    def authorize(self, identity_id: UUID, organisation_id: UUID, permission: str) -> bool:
        return permission in self.effective_permissions(identity_id, organisation_id)

    # Phase 2.5 â€” Module registry and organisation entitlements

    def register_module(self, code: str, name: str, version: str):
        return self.module_service.register(code, name, version)

    def get_module(self, module_id: UUID):
        return self.module_service.get(module_id)

    def get_module_by_code(self, code: str):
        return self.module_service.get_by_code(code)

    def list_modules(self, *, status: str | None = None):
        return self.module_service.list(status=status)

    def set_module_status(self, module_id: UUID, status: str):
        return self.module_service.set_status(module_id, status)

    def enable_module(self, module_id: UUID):
        return self.module_service.enable(module_id)

    def disable_module(self, module_id: UUID):
        return self.module_service.disable(module_id)

    def retire_module(self, module_id: UUID):
        return self.module_service.retire(module_id)

    def grant_module_entitlement(self, organisation_id: UUID, module_id: UUID):
        return self.entitlement_service.grant(organisation_id, module_id)

    def get_module_entitlement(self, entitlement_id: UUID):
        return self.entitlement_service.get(entitlement_id)

    def get_organisation_module_entitlement(
        self, organisation_id: UUID, module_id: UUID
    ):
        return self.entitlement_service.get_for_organisation_module(
            organisation_id, module_id
        )

    def list_module_entitlements(
        self, organisation_id: UUID, *, status: str | None = None
    ):
        return self.entitlement_service.list_for_organisation(
            organisation_id, status=status
        )

    def set_module_entitlement_status(
        self, entitlement_id: UUID, status: str
    ):
        return self.entitlement_service.set_status(entitlement_id, status)

    def suspend_module_entitlement(self, entitlement_id: UUID):
        return self.entitlement_service.suspend(entitlement_id)

    def activate_module_entitlement(self, entitlement_id: UUID):
        return self.entitlement_service.activate(entitlement_id)

    def revoke_module_entitlement(self, entitlement_id: UUID):
        return self.entitlement_service.revoke(entitlement_id)

    def module_available(
        self, organisation_id: UUID, module_id: UUID
    ) -> bool:
        return self.entitlement_service.is_module_available(
            organisation_id, module_id
        )

    def has_capability(
        self,
        identity_id: UUID,
        organisation_id: UUID,
        permission: str,
        module_id: UUID,
    ) -> bool:
        if not self.module_available(organisation_id, module_id):
            return False

        membership = self.db.execute(
            """
            SELECT 1
            FROM organisation_memberships
            WHERE identity_id=?
              AND organisation_id=?
              AND status='ACTIVE'
            """,
            (str(identity_id), str(organisation_id)),
        ).fetchone()

        if not membership:
            return False

        return self.authorize(identity_id, organisation_id, permission)
    def create_setting(self, key, value, value_type="STRING", *, organisation_id=None, description=None):
        return self.configuration_service.create_setting(key, value, value_type, organisation_id=organisation_id, description=description)

    def get_setting(self, key, *, organisation_id=None, required=True):
        return self.configuration_service.get_setting(key, organisation_id=organisation_id, required=required)

    def get_effective_setting(self, key, *, organisation_id=None, required=True):
        return self.configuration_service.get_effective_setting(key, organisation_id=organisation_id, required=required)

    def list_settings(self, *, organisation_id=None, include_global=False):
        return self.configuration_service.list_settings(organisation_id=organisation_id, include_global=include_global)

    def create_feature_flag(self, key, enabled=False, *, organisation_id=None, description=None):
        return self.configuration_service.create_feature_flag(key, enabled, organisation_id=organisation_id, description=description)

    def set_feature_flag(self, key, enabled, *, organisation_id=None):
        return self.configuration_service.set_feature_flag(key, enabled, organisation_id=organisation_id)

    def get_feature_flag(self, key, *, organisation_id=None, required=True):
        return self.configuration_service.get_feature_flag(key, organisation_id=organisation_id, required=required)

    def is_feature_enabled(self, key, *, organisation_id=None):
        return self.configuration_service.is_feature_enabled(key, organisation_id=organisation_id)

    def record_audit(self, event: AuditEvent):
        """Compatibility facade for the authoritative Core audit service."""
        return self.audit_service.record(event)

    def get_audit_event(self, event_id: UUID):
        return self.audit_service.get(event_id)

    def list_audit_events(
        self,
        *,
        organisation_id: UUID | None = None,
        identity_id: UUID | None = None,
        action: str | None = None,
        target_type: str | None = None,
        target_id: UUID | None = None,
        request_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return self.audit_service.list(
            organisation_id=organisation_id,
            identity_id=identity_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            request_id=request_id,
            limit=limit,
            offset=offset,
        )


