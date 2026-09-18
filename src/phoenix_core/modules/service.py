"""Phoenix Core V2 module registry application service."""

from uuid import UUID

from phoenix_core.errors import ConflictError, NotFoundError, ValidationError
from phoenix_core.modules.domain import Module


class ModuleService:
    """Operational service for the authoritative Core module registry."""

    VALID_STATUSES = {"REGISTERED", "ENABLED", "DISABLED", "RETIRED"}

    def __init__(self, db):
        self.db = db

    def register(self, code: str, name: str, version: str) -> Module:
        module = Module.create(code, name, version)
        try:
            self.db.execute(
                "INSERT INTO modules(id,code,name,version,status,created_at) VALUES (?,?,?,?,?,?)",
                (str(module.id), module.code, module.name, module.version,
                 module.status, module.created_at.isoformat()),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError("Module code already exists.") from exc
            raise
        return module

    def get(self, module_id: UUID) -> Module:
        row = self.db.execute(
            "SELECT id,code,name,version,status,created_at FROM modules WHERE id=?",
            (str(module_id),),
        ).fetchone()
        if not row:
            raise NotFoundError("Module not found.")
        from datetime import datetime
        return Module(
            UUID(row["id"]), row["code"], row["name"], row["version"],
            row["status"], datetime.fromisoformat(row["created_at"]),
        )

    def get_by_code(self, code: str) -> Module:
        code = (code or "").strip().lower()
        if not code:
            raise ValidationError("Module code is required.")
        row = self.db.execute(
            "SELECT id,code,name,version,status,created_at FROM modules WHERE code=?",
            (code,),
        ).fetchone()
        if not row:
            raise NotFoundError("Module not found.")
        from datetime import datetime
        return Module(
            UUID(row["id"]), row["code"], row["name"], row["version"],
            row["status"], datetime.fromisoformat(row["created_at"]),
        )

    def list(self, *, status: str | None = None) -> list[Module]:
        if status is not None and status not in self.VALID_STATUSES:
            raise ValidationError("Invalid module status.")
        sql = "SELECT id,code,name,version,status,created_at FROM modules"
        params = []
        if status is not None:
            sql += " WHERE status=?"
            params.append(status)
        sql += " ORDER BY code"
        rows = self.db.execute(sql, params).fetchall()
        from datetime import datetime
        return [
            Module(UUID(r["id"]), r["code"], r["name"], r["version"],
                   r["status"], datetime.fromisoformat(r["created_at"]))
            for r in rows
        ]

    def set_status(self, module_id: UUID, status: str) -> Module:
        if status not in self.VALID_STATUSES:
            raise ValidationError("Invalid module status.")
        current = self.get(module_id)
        if current.status == status:
            return current

        allowed = {
            "REGISTERED": {"ENABLED", "DISABLED", "RETIRED"},
            "ENABLED": {"DISABLED", "RETIRED"},
            "DISABLED": {"ENABLED", "RETIRED"},
            "RETIRED": set(),
        }
        if status not in allowed[current.status]:
            raise ValidationError(
                f"Module cannot transition from {current.status} to {status}."
            )

        self.db.execute(
            "UPDATE modules SET status=? WHERE id=?",
            (status, str(module_id)),
        )
        self.db.commit()
        return self.get(module_id)

    def enable(self, module_id: UUID) -> Module:
        return self.set_status(module_id, "ENABLED")

    def disable(self, module_id: UUID) -> Module:
        return self.set_status(module_id, "DISABLED")

    def retire(self, module_id: UUID) -> Module:
        return self.set_status(module_id, "RETIRED")
