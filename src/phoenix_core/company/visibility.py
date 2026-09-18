"""Tenant-scoped Company Platform data visibility policy service."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from phoenix_core.errors import AuthorizationError, NotFoundError, ValidationError


class CompanyVisibilityService:
    """Manages company visibility restrictions without replacing Core authorization."""

    VALID_SCOPES = {"MEMBERSHIP", "ROLE"}

    def __init__(self, db):
        self.db = db

    def _ensure_table(self):
        if not self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='company_visibility_rules'").fetchone():
            raise ValidationError("Company visibility schema is not installed. Apply migration 013_company_platform_data_visibility.sql.")

    def list(self, organisation_id: UUID):
        self._ensure_table()
        rows = self.db.execute(
            "SELECT * FROM company_visibility_rules WHERE organisation_id=? ORDER BY resource_code, scope_type, id",
            (str(organisation_id),),
        ).fetchall()
        return [self._row(row) for row in rows]

    def upsert(self, organisation_id: UUID, *, scope_type: str, resource_code: str,
               visible: bool, membership_id: UUID | None = None, role_id: UUID | None = None):
        self._ensure_table()
        if scope_type not in self.VALID_SCOPES:
            raise ValidationError("Invalid visibility scope.")
        resource_code = (resource_code or "").strip().lower()
        if not resource_code or any(ch.isspace() for ch in resource_code):
            raise ValidationError("Resource code is required and cannot contain whitespace.")
        if not isinstance(visible, bool):
            raise ValidationError("Visibility must be boolean.")
        if scope_type == "MEMBERSHIP":
            if membership_id is None or role_id is not None:
                raise ValidationError("Membership scope requires membership_id only.")
            membership = self.db.execute(
                "SELECT organisation_id,status FROM organisation_memberships WHERE id=?", (str(membership_id),)
            ).fetchone()
            if not membership or membership["organisation_id"] != str(organisation_id):
                raise AuthorizationError("Membership does not belong to the current organisation.")
        else:
            if role_id is None or membership_id is not None:
                raise ValidationError("Role scope requires role_id only.")
            role = self.db.execute("SELECT organisation_id,scope,status FROM roles WHERE id=?", (str(role_id),)).fetchone()
            if not role or role["organisation_id"] != str(organisation_id):
                raise AuthorizationError("Role does not belong to the current organisation.")
            if role["scope"] != "ORGANISATION":
                raise AuthorizationError("Only organisation roles can receive company visibility rules.")

        subject = str(membership_id) if membership_id else str(role_id)
        now = datetime.now(timezone.utc).isoformat()
        current = self.db.execute(
            "SELECT id FROM company_visibility_rules WHERE organisation_id=? AND scope_type=? AND COALESCE(membership_id,'')=COALESCE(?, '') AND COALESCE(role_id,'')=COALESCE(?, '') AND resource_code=?",
            (str(organisation_id), scope_type, str(membership_id) if membership_id else None,
             str(role_id) if role_id else None, resource_code),
        ).fetchone()
        if current:
            self.db.execute("UPDATE company_visibility_rules SET visible=?, updated_at=? WHERE id=?", (int(visible), now, current["id"]))
            rule_id = current["id"]
        else:
            rule_id = str(uuid4())
            self.db.execute(
                "INSERT INTO company_visibility_rules(id,organisation_id,scope_type,membership_id,role_id,resource_code,visible,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (rule_id, str(organisation_id), scope_type, str(membership_id) if membership_id else None,
                 str(role_id) if role_id else None, resource_code, int(visible), now, now),
            )
        self.db.commit()
        row = self.db.execute("SELECT * FROM company_visibility_rules WHERE id=?", (rule_id,)).fetchone()
        return self._row(row)

    def delete(self, organisation_id: UUID, rule_id: UUID):
        self._ensure_table()
        row = self.db.execute("SELECT organisation_id FROM company_visibility_rules WHERE id=?", (str(rule_id),)).fetchone()
        if not row:
            raise NotFoundError("Visibility rule not found.")
        if row["organisation_id"] != str(organisation_id):
            raise AuthorizationError("Visibility rule does not belong to the current organisation.")
        self.db.execute("DELETE FROM company_visibility_rules WHERE id=?", (str(rule_id),))
        self.db.commit()
        return True

    def is_visible(self, organisation_id: UUID, identity_id: UUID, resource_code: str) -> bool:
        """Return visibility after Core permission checks have already succeeded.

        No explicit rule means visible. Any applicable DENY overrides an ALLOW.
        Membership-specific rules override role rules when both explicitly deny/allow.
        """
        self._ensure_table()
        resource_code = (resource_code or "").strip().lower()
        membership = self.db.execute(
            "SELECT id FROM organisation_memberships WHERE identity_id=? AND organisation_id=? AND status='ACTIVE'",
            (str(identity_id), str(organisation_id)),
        ).fetchone()
        if not membership:
            return False
        rows = self.db.execute(
            "SELECT visible FROM company_visibility_rules WHERE organisation_id=? AND resource_code=? AND (membership_id=? OR role_id IN (SELECT ra.role_id FROM role_assignments ra WHERE ra.membership_id=?)) ORDER BY CASE WHEN membership_id IS NOT NULL THEN 0 ELSE 1 END",
            (str(organisation_id), resource_code, str(membership["id"]), str(membership["id"])),
        ).fetchall()
        if any(not bool(row["visible"]) for row in rows):
            return False
        return True

    @staticmethod
    def _row(row):
        return {
            "id": str(row["id"]),
            "organisation_id": str(row["organisation_id"]),
            "scope_type": row["scope_type"],
            "membership_id": row["membership_id"],
            "role_id": row["role_id"],
            "resource_code": row["resource_code"],
            "visible": bool(row["visible"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
