# Phoenix Company Platform — Data Visibility V1

## Boundary

Company Platform Data Visibility defines tenant-level visibility restrictions for company resources. It does not replace Phoenix Core authentication, permissions, memberships, roles, or module entitlements.

## Security model

```text
Phoenix Core permission
        ↓
Company visibility policy
        ↓
Module/resource query
```

A visibility rule can narrow access for an authorised user. A hidden/denied resource must never become accessible merely because the frontend shows it. Modules must consult the Core-owned visibility policy when enforcing resource-level visibility.

## Scopes

- `ROLE` — applies to an organisation role.
- `MEMBERSHIP` — applies to one company membership/user.

Only organisation-scoped roles and memberships belonging to the current tenant may be configured.

## Resources

Resource identifiers are stable application-level codes, for example `customers`, `inventory`, or `production`. Business modules own the meaning of their resources; Company Platform owns the tenant visibility policy.

## Default behaviour

No explicit visibility rule means the resource remains visible to a user who already has the required Core permission. An explicit hidden rule narrows visibility. Any applicable hidden rule denies visibility.

## API

- `GET /api/v1/company/visibility`
- `PUT /api/v1/company/visibility`
- `DELETE /api/v1/company/visibility/{rule_id}`

Mutations require `company.visibility.manage`, are tenant-scoped, and create Core audit events.

## Migration

Apply `migrations/013_company_platform_data_visibility.sql` after the existing Core and Company Platform migrations.
