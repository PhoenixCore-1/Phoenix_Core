"""Tenant-scoped Company Platform workspace configuration."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from phoenix_core.errors import AuthorizationError, NotFoundError, ValidationError


class CompanyWorkspaceService:
    """Persists company workspace presentation settings; Core remains authoritative for access."""

    def __init__(self, db, module_service, entitlement_service):
        self.db = db
        self.module_service = module_service
        self.entitlement_service = entitlement_service

    def _ensure_table(self):
        # Runtime environments should apply migrations centrally; this guard only gives
        # development/test databases a clear failure rather than silently creating schema.
        row = self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='company_workspaces'").fetchone()
        if not row:
            raise ValidationError("Company workspace schema is not installed. Apply migration 012_company_platform_workspaces.sql.")

    def list(self, organisation_id: UUID):
        self._ensure_table()
        entitlements = self.entitlement_service.list_for_organisation(organisation_id, status="ACTIVE")
        rows = self.db.execute(
            "SELECT * FROM company_workspaces WHERE organisation_id=? ORDER BY sort_order, display_name, id",
            (str(organisation_id),),
        ).fetchall()
        by_module = {r["module_id"]: r for r in rows}
        items = []
        for entitlement in entitlements:
            module = self.module_service.get(entitlement.module_id)
            row = by_module.get(str(module.id))
            items.append({
                "id": str(UUID(row["id"])) if row else None,
                "module_id": str(module.id),
                "module_code": module.code,
                "module_name": module.name,
                "module_version": module.version,
                "display_name": row["display_name"] if row else module.name,
                "visible": bool(row["visible"]) if row else True,
                "sort_order": int(row["sort_order"]) if row else len(items),
                "entitlement_status": entitlement.status,
            })
        return sorted(items, key=lambda item: (item["sort_order"], item["display_name"].lower()))

    def update(self, organisation_id: UUID, module_code: str, *, display_name=None, visible=None, sort_order=None):
        self._ensure_table()
        module = self.module_service.get_by_code(module_code)
        if not self.entitlement_service.is_module_available(organisation_id, module.id):
            raise AuthorizationError("The module is not active for the current organisation.")
        if display_name is not None:
            display_name = display_name.strip()
            if not display_name:
                raise ValidationError("Workspace display name is required.")
        if visible is not None and not isinstance(visible, bool):
            raise ValidationError("Workspace visible must be boolean.")
        if sort_order is not None:
            if isinstance(sort_order, bool) or not isinstance(sort_order, int) or sort_order < 0:
                raise ValidationError("Workspace sort order must be a non-negative integer.")
        current = self.db.execute(
            "SELECT * FROM company_workspaces WHERE organisation_id=? AND module_id=?",
            (str(organisation_id), str(module.id)),
        ).fetchone()
        now = datetime.now(timezone.utc).isoformat()
        if current:
            new_name = current["display_name"] if display_name is None else display_name
            new_visible = int(current["visible"]) if visible is None else int(visible)
            new_order = int(current["sort_order"]) if sort_order is None else sort_order
            self.db.execute(
                "UPDATE company_workspaces SET display_name=?, visible=?, sort_order=?, updated_at=? WHERE id=?",
                (new_name, new_visible, new_order, now, current["id"]),
            )
            workspace_id = current["id"]
        else:
            workspace_id = str(uuid4())
            self.db.execute(
                "INSERT INTO company_workspaces(id,organisation_id,module_id,display_name,visible,sort_order,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (workspace_id, str(organisation_id), str(module.id), display_name or module.name,
                 1 if visible is None else int(visible), 0 if sort_order is None else sort_order, now, now),
            )
        self.db.commit()
        return next(item for item in self.list(organisation_id) if item["module_code"] == module.code)
