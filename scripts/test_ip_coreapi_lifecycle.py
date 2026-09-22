import sqlite3
from uuid import UUID, uuid4

from phoenix_core.api.application import CoreApi
from phoenix_core.errors import AuthorizationError

DB = ".local/phoenix_core_v1_dev.db"

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

api = CoreApi(db)

org = db.execute(
    "SELECT id FROM organisations WHERE code='DEMO' LIMIT 1"
).fetchone()

if not org:
    raise RuntimeError("DEMO organisation not found.")

org_id = UUID(org["id"])
other_org_id = uuid4()

print(f"Organisation: {org_id}")
print(f"Other organisation: {other_org_id}")
print()

# Authenticate through the real Phoenix authentication service.
auth = api.authenticate(
    request_id=str(uuid4()),
    username="demo.user",
    password="Phoenix-V1-User-2026!",
    organisation_id=org_id,
)

session_id = UUID(auth.data["session_id"])

print("Authenticated session:", session_id)

# Resolve the real authenticated RequestContext.
context = api.resolve_context(
    request_id=str(uuid4()),
    session_id=session_id,
    organisation_id=org_id,
)

print("Authenticated Core context: OK")
print("Identity:", context.identity_id)
print("Organisation:", context.organisation_id)

# The current development user may not have the new permission assigned.
# Test the underlying CoreApi service contract first, without weakening
# production authorization.
owner = api.ip_ownership_service.create_owner(
    owner_type="COMPANY",
    name="Demo Company IP Owner",
    organisation_id=org_id,
)

print("1. Company owner created:", owner["id"])

asset = api.ip_ownership_service.create_asset(
    owner_id=owner["id"],
    asset_code="DEMO-CORE-IP-001",
    name="Phoenix Demo Customer Content",
    asset_type="CUSTOMER_CONTENT",
    confidentiality_class="CONFIDENTIAL",
    organisation_id=org_id,
)

print("2. Asset created:", asset["id"])

loaded = api.ip_ownership_service.get_asset(
    asset["id"],
    organisation_id=org_id,
)

assert loaded["id"] == asset["id"]
print("3. Asset retrieval: OK")

new_owner = api.ip_ownership_service.create_owner(
    owner_type="COMPANY",
    name="Demo Company IP Custodian",
    organisation_id=org_id,
)

transfer = api.ip_ownership_service.record_ownership_transfer(
    asset["id"],
    new_owner_id=new_owner["id"],
    organisation_id=org_id,
    reason="CoreApi lifecycle test",
    created_by_identity_id=context.identity_id,
)

assert transfer["asset"]["owner_id"] == new_owner["id"]
print("4. Ownership transfer: OK")

licence = api.ip_ownership_service.create_licence(
    asset["id"],
    licence_type="CUSTOMER",
    organisation_id=org_id,
    licence_name="Demo Customer Licence",
    permitted_use="ERP customer operations",
)

print("5. Licence created:", licence["id"])

component = api.ip_ownership_service.register_third_party_component(
    asset["id"],
    component_name="Test Dependency",
    component_version="1.0.0",
    supplier="Test Supplier",
    organisation_id=org_id,
)

print("6. Third-party component:", component["id"])

try:
    api.ip_ownership_service.get_asset(
        asset["id"],
        organisation_id=other_org_id,
    )
    raise AssertionError("Cross-tenant access was not rejected.")
except AuthorizationError:
    print("7. Cross-tenant access rejected: OK")

events = db.execute(
    """
    SELECT event_type
    FROM ip_ownership_events
    WHERE asset_id=?
    ORDER BY created_at
    """,
    (asset["id"],),
).fetchall()

event_types = [row["event_type"] for row in events]

assert "CREATED" in event_types
assert "TRANSFERRED" in event_types

print("8. Ownership history: OK")

# Revoke the test session through the real API.
api.revoke_session(
    request_id=str(uuid4()),
    token=auth.data["token"],
)

print("9. Test session revoked: OK")

print()
print("CORE API IP LIFECYCLE TEST: PASSED")

db.close()

