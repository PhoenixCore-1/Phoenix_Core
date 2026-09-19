from pathlib import Path
import sqlite3
import json
import urllib.request
import urllib.error
import http.cookiejar
from uuid import uuid4

BASE = "http://127.0.0.1:8000"
DB = Path(".local/phoenix_core_v1_dev.db")


def request(opener, method, path, body=None):
    data = None
    headers = {}

    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with opener.open(req) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return error.code, payload


db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

org = db.execute(
    "SELECT id FROM organisations WHERE code='DEMO'"
).fetchone()

if not org:
    raise RuntimeError("DEMO organisation not found.")

org_id = org["id"]

identity = db.execute(
    "SELECT identity_id FROM users WHERE username='demo.user'"
).fetchone()

if not identity:
    raise RuntimeError("demo.user not found.")

identity_id = identity["identity_id"]

document_id = str(uuid4())
document_version_id = str(uuid4())
checksum = f"ip-version-test-{uuid4().hex}"

db.execute(
    """
    INSERT INTO documents(
        id, organisation_id, name, description,
        mime_type, size_bytes, storage_key, checksum,
        context_type, context_id, status,
        created_by_identity_id, created_at, updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """,
    (
        document_id,
        org_id,
        "IP Version Test Evidence",
        "Asset version lifecycle test",
        "application/pdf",
        1,
        f"ip-version-test/{document_id}",
        checksum,
        "IP_ASSET",
        None,
        "ACTIVE",
        identity_id,
    ),
)

db.execute(
    """
    INSERT INTO document_versions(
        id, document_id, version_number, storage_key,
        mime_type, size_bytes, checksum,
        created_by_identity_id, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """,
    (
        document_version_id,
        document_id,
        1,
        f"ip-version-test/{document_id}/v1",
        "application/pdf",
        1,
        checksum,
        identity_id,
    ),
)

db.commit()
db.close()

print(f"DEMO organisation: {org_id}")

client = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
)

print("\n1. Login...")

status, payload = request(
    client,
    "POST",
    "/api/v1/auth/login",
    {
        "username": "demo.user",
        "password": "Phoenix-V1-User-2026!",
        "organisation_id": org_id,
    },
)

if status != 200:
    raise RuntimeError(f"Login failed: {status} {payload}")

print("Login: OK")

print("\n2. Create IP owner...")

status, payload = request(
    client,
    "POST",
    "/api/ip/owners",
    {
        "owner_type": "COMPANY",
        "name": "IP Version Test Owner",
        "description": "Asset version lifecycle test",
    },
)

if status != 200:
    raise RuntimeError(f"Owner failed: {status} {payload}")

owner_id = payload["id"]

print(f"Owner: {owner_id}")

print("\n3. Create IP asset...")

status, payload = request(
    client,
    "POST",
    "/api/ip/assets",
    {
        "owner_id": owner_id,
        "asset_code": f"IP-VERSION-{uuid4().hex[:8]}",
        "name": "IP Version Test Asset",
        "description": "Asset version lifecycle test",
        "asset_type": "SOFTWARE",
        "confidentiality_class": "CONFIDENTIAL",
    },
)

if status != 200:
    raise RuntimeError(f"Asset failed: {status} {payload}")

asset_id = payload["id"]

print(f"Asset: {asset_id}")

print("\n4. Create asset version...")

status, payload = request(
    client,
    "POST",
    f"/api/ip/assets/{asset_id}/versions",
    {
        "version_label": "1.0.0",
        "description": "Initial IP asset version",
        "document_id": document_id,
        "document_version_id": document_version_id,
        "checksum": checksum,
        "effective_from": "2026-09-19T00:00:00",
    },
)

if status != 200:
    raise RuntimeError(f"Version creation failed: {status} {payload}")

version_id = payload["id"]

print(f"Version: {version_id}")

print("\n5. Retrieve asset version...")

status, payload = request(
    client,
    "GET",
    f"/api/ip/asset-versions/{version_id}",
)

if status != 200:
    raise RuntimeError(f"Version retrieval failed: {status} {payload}")

if payload["id"] != version_id:
    raise RuntimeError("Version ID mismatch.")

print("Version retrieval: OK")

print("\n6. List asset versions...")

status, payload = request(
    client,
    "GET",
    f"/api/ip/assets/{asset_id}/versions",
)

if status != 200:
    raise RuntimeError(f"Version listing failed: {status} {payload}")

if not any(item["id"] == version_id for item in payload["items"]):
    raise RuntimeError("Created version missing from asset version list.")

print("Version listing: OK")

print("\n7. Retire asset version...")

status, payload = request(
    client,
    "POST",
    f"/api/ip/asset-versions/{version_id}/retire",
    {
        "retired_at": "2026-09-19T23:59:59",
    },
)

if status != 200:
    raise RuntimeError(f"Version retirement failed: {status} {payload}")

if not payload.get("retired_at"):
    raise RuntimeError("Version was not marked retired.")

print("Version retirement: OK")

print("\n8. Verify retired version...")

status, payload = request(
    client,
    "GET",
    f"/api/ip/asset-versions/{version_id}",
)

if status != 200:
    raise RuntimeError(
        f"Retired version retrieval failed: {status} {payload}"
    )

if not payload.get("retired_at"):
    raise RuntimeError("Retired timestamp missing.")

print("Retirement verification: OK")

print("\nIP ASSET VERSION HTTP LIFECYCLE TEST: PASSED")
