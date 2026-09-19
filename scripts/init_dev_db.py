"""Create a clean Phoenix Core V1.0.0 development database."""
from pathlib import Path
from uuid import UUID, uuid4
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.services import CoreFoundationService
from phoenix_core.migration_runner import apply_all

ROOT = Path(__file__).resolve().parents[1]
DB_DIR = ROOT / ".local"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "phoenix_core_v1_dev.db"

if DB_PATH.exists():
    DB_PATH.unlink()

db = SQLiteDatabase(DB_PATH)
apply_all(db)
core = CoreFoundationService(db)

system = core.create_user("system.admin", "Phoenix System Administrator", "Phoenix-V1-System-2026!")
db.execute("UPDATE users SET platform_level='SYSTEM_ADMIN' WHERE id=?", (str(system.id),))

company = core.create_organisation("DEMO", "Phoenix Demo Company")
admin = core.create_user("company.admin", "Company Administrator", "Phoenix-V1-Company-2026!")
db.execute("UPDATE users SET platform_level='COMPANY_ADMIN' WHERE id=?", (str(admin.id),))
core.add_membership(admin.identity_id, company.id)

user = core.create_user("demo.user", "Demo User", "Phoenix-V1-User-2026!")
core.add_membership(user.identity_id, company.id)

# Development IP management role.
ip_role = core.create_role(
    company.id,
    "demo.ip.manager",
    "Demo IP Manager",
    scope="ORGANISATION",
)

for permission_code in (
    "system.ip_management.view",
    "system.ip_management.manage",
):
    permission = core.get_permission_by_code(permission_code)
    core.grant_permission(ip_role.id, permission.id)

user_membership = db.execute(
    """
    SELECT id
    FROM organisation_memberships
    WHERE identity_id=? AND organisation_id=?
    """,
    (str(user.identity_id), str(company.id)),
).fetchone()

if not user_membership:
    raise RuntimeError("Demo user membership was not created.")

core.assign_role(
    UUID(user_membership["id"]),
    ip_role.id,
)

module_id = uuid4()
db.execute(
    "INSERT INTO modules(id,code,name,version,status,created_at) VALUES (?,?,?,?,?,CURRENT_TIMESTAMP)",
    (str(module_id), "sales_360", "Sales 360", "0.1.0", "ENABLED"),
)
core.grant_module_entitlement(company.id, module_id)
db.commit()
db.close()

print(f"Initialized {DB_PATH}")
print("System:  system.admin / Phoenix-V1-System-2026!")
print("Company: company.admin / Phoenix-V1-Company-2026!")
print("User:    demo.user / Phoenix-V1-User-2026!")
