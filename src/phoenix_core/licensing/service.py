"""Phoenix Core V2 organisation module entitlement service."""

from uuid import UUID

from phoenix_core.errors import AuthorizationError, ConflictError, NotFoundError, ValidationError
from phoenix_core.licensing.domain import Entitlement


class EntitlementService:
    """Authoritative Core service for organisation/module entitlements."""

    VALID_STATUSES = {"ACTIVE", "SUSPENDED", "REVOKED"}

    def __init__(self, db):
        self.db = db

    def grant(self, organisation_id: UUID, module_id: UUID) -> Entitlement:
        org = self.db.execute(
            "SELECT status FROM organisations WHERE id=?",
            (str(organisation_id),),
        ).fetchone()
        if not org:
            raise NotFoundError("Organisation not found.")
        if org["status"] != "ACTIVE":
            raise AuthorizationError("Entitlement can only be granted to an active organisation.")

        module = self.db.execute(
            "SELECT status FROM modules WHERE id=?",
            (str(module_id),),
        ).fetchone()
        if not module:
            raise NotFoundError("Module not found.")
        if module["status"] == "RETIRED":
            raise ValidationError("Retired modules cannot be entitled.")

        entitlement = Entitlement.grant(organisation_id, module_id)
        try:
            self.db.execute(
                "INSERT INTO module_entitlements(id,organisation_id,module_id,status,created_at) "
                "VALUES (?,?,?,?,?)",
                (str(entitlement.id), str(entitlement.organisation_id),
                 str(entitlement.module_id), entitlement.status,
                 entitlement.created_at.isoformat()),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError("Organisation is already entitled to this module.") from exc
            raise
        return entitlement

    def get(self, entitlement_id: UUID) -> Entitlement:
        row = self.db.execute(
            "SELECT id,organisation_id,module_id,status,created_at "
            "FROM module_entitlements WHERE id=?",
            (str(entitlement_id),),
        ).fetchone()
        if not row:
            raise NotFoundError("Entitlement not found.")
        from datetime import datetime
        return Entitlement(
            UUID(row["id"]), UUID(row["organisation_id"]), UUID(row["module_id"]),
            row["status"], datetime.fromisoformat(row["created_at"]),
        )

    def get_for_organisation_module(
        self, organisation_id: UUID, module_id: UUID
    ) -> Entitlement:
        row = self.db.execute(
            "SELECT id,organisation_id,module_id,status,created_at "
            "FROM module_entitlements WHERE organisation_id=? AND module_id=?",
            (str(organisation_id), str(module_id)),
        ).fetchone()
        if not row:
            raise NotFoundError("Module entitlement not found.")
        from datetime import datetime
        return Entitlement(
            UUID(row["id"]), UUID(row["organisation_id"]), UUID(row["module_id"]),
            row["status"], datetime.fromisoformat(row["created_at"]),
        )

    def list_for_organisation(
        self, organisation_id: UUID, *, status: str | None = None
    ) -> list[Entitlement]:
        if not self.db.execute(
            "SELECT 1 FROM organisations WHERE id=?", (str(organisation_id),)
        ).fetchone():
            raise NotFoundError("Organisation not found.")
        if status is not None and status not in self.VALID_STATUSES:
            raise ValidationError("Invalid entitlement status.")
        sql = (
            "SELECT id,organisation_id,module_id,status,created_at "
            "FROM module_entitlements WHERE organisation_id=?"
        )
        params = [str(organisation_id)]
        if status is not None:
            sql += " AND status=?"
            params.append(status)
        sql += " ORDER BY created_at,id"
        rows = self.db.execute(sql, params).fetchall()
        from datetime import datetime
        return [
            Entitlement(UUID(r["id"]), UUID(r["organisation_id"]), UUID(r["module_id"]),
                        r["status"], datetime.fromisoformat(r["created_at"]))
            for r in rows
        ]

    def set_status(self, entitlement_id: UUID, status: str) -> Entitlement:
        if status not in self.VALID_STATUSES:
            raise ValidationError("Invalid entitlement status.")
        current = self.get(entitlement_id)
        if current.status == status:
            return current

        allowed = {
            "ACTIVE": {"SUSPENDED", "REVOKED"},
            "SUSPENDED": {"ACTIVE", "REVOKED"},
            "REVOKED": set(),
        }
        if status not in allowed[current.status]:
            raise ValidationError(
                f"Entitlement cannot transition from {current.status} to {status}."
            )

        self.db.execute(
            "UPDATE module_entitlements SET status=? WHERE id=?",
            (status, str(entitlement_id)),
        )
        self.db.commit()
        return self.get(entitlement_id)

    def suspend(self, entitlement_id: UUID) -> Entitlement:
        return self.set_status(entitlement_id, "SUSPENDED")

    def revoke(self, entitlement_id: UUID) -> Entitlement:
        return self.set_status(entitlement_id, "REVOKED")

    def activate(self, entitlement_id: UUID) -> Entitlement:
        return self.set_status(entitlement_id, "ACTIVE")

    def is_module_available(self, organisation_id: UUID, module_id: UUID) -> bool:
        org = self.db.execute(
            "SELECT status FROM organisations WHERE id=?",
            (str(organisation_id),),
        ).fetchone()
        module = self.db.execute(
            "SELECT status FROM modules WHERE id=?",
            (str(module_id),),
        ).fetchone()
        entitlement = self.db.execute(
            "SELECT status FROM module_entitlements "
            "WHERE organisation_id=? AND module_id=?",
            (str(organisation_id), str(module_id)),
        ).fetchone()
        return bool(
            org and org["status"] == "ACTIVE"
            and module and module["status"] == "ENABLED"
            and entitlement and entitlement["status"] == "ACTIVE"
        )
