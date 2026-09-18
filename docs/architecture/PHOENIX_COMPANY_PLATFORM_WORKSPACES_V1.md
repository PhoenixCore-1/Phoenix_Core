# Phoenix Company Platform — Workspaces V1

## Boundary

Company Platform Workspaces controls the tenant-facing presentation and ordering of workspaces for modules that are already active for the company.

It does **not** activate, deactivate, license, revoke, upgrade, or downgrade modules. Those decisions remain owned by Phoenix System Platform and Phoenix Core entitlements.

## Authority

```text
Phoenix Core
  ├─ Identity / session
  ├─ Organisation / membership
  ├─ Permissions
  ├─ Module registry
  └─ Module entitlements
          ↓
Company Platform
  └─ Workspace presentation configuration
          ↓
User Platform / Business Modules
```

## API

- `GET /api/v1/company/workspaces`
- `PATCH /api/v1/company/workspaces/{module_code}`

The GET endpoint returns only modules with an active Core entitlement. The PATCH endpoint requires `company.workspaces.manage` and rejects modules that are not active for the current organisation.

## Configuration

Company workspace configuration contains:

- display name
- visible/hidden presentation state
- sort order
- linked Core module
- Core entitlement status

A hidden workspace is a presentation choice. It is **not** a security boundary and must never be treated as permission enforcement. Effective access remains server-side in Phoenix Core.

## Audit

Workspace mutations create `COMPANY_WORKSPACE_UPDATED` audit events using the current organisation, authenticated identity, module target and request/correlation ID.

## Migration

Apply `migrations/012_company_platform_workspaces.sql` after the existing Core migrations before using the workspace API.
