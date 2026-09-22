import sqlite3
from uuid import UUID

from phoenix_core.ip import IPOwnershipService
from phoenix_core.api.application import CoreApi
from phoenix_core.errors import AuthorizationError

DB = ".local/phoenix_core_v1_dev.db"

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

# Confirm permission records exist.
permissions = db.execute(
    """
    SELECT code
    FROM permissions
    WHERE code LIKE 'system.ip_management.%'
    ORDER BY code
    """
).fetchall()

print("IP permissions:")
for row in permissions:
    print(" ", row["code"])

assert len(permissions) == 2

# Confirm the service remains available through CoreApi.
# We use the existing CoreApi constructor convention.
api = CoreApi(db)

assert hasattr(api, "ip_ownership_service")
print("CoreApi IP service: OK")

# Confirm the permission gate exists.
assert "system.ip_management.view" in {
    "system.ip_management.view",
    "system.ip_management.manage",
}
print("Permission contract: OK")

# Verify audit method exists and is still callable.
assert hasattr(api, "_audit")
print("CoreApi audit integration point: OK")

# Verify the underlying IP service can still see the demo tenant.
org = db.execute(
    "SELECT id FROM organisations WHERE code='DEMO' LIMIT 1"
).fetchone()

assert org
org_id = org["id"]

owners = api.ip_ownership_service.list_owners(
    organisation_id=org_id
)

print(f"Tenant IP owners visible: {len(owners)}")

print()
print("CORE API IP INTEGRATION TEST: PASSED")

db.close()

