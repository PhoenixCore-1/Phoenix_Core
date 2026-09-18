# Phase 2.6 — Core Audit & Event Foundation

## Status
Implementation package for Phoenix Core V2 Phase 2.6.

## Authority
Audit events are Core-owned, append-only records. The authoritative persistence
table is `audit_events` in the V2 Core schema.

Business modules must emit events through a Core audit contract/service and must
not access the Core database or `audit_events` directly.

## Scope
- Dedicated `AuditService`
- Append-only audit recording
- Audit event lookup
- Organisation and identity scoped retrieval
- Action, target and request correlation filters
- Bounded pagination
- Validation of referenced organisations and identities
- Core facade integration
- Tenant-scoped retrieval
- Tests for isolation and append-only behavior

## Existing schema
No migration is required for Phase 2.6. The existing V2 `audit_events` table is
sufficient for this phase.

## Boundary
`Module / Platform -> Core audit contract -> AuditService -> Core persistence`

No module is permitted to bypass the Core audit boundary.

## Event semantics
An audit event records an occurrence; it is not a mutable business record.
There are intentionally no update or delete operations in `AuditService`.
Corrections are represented by subsequent events.

## Retrieval
`list()` supports:
- organisation_id
- identity_id
- action
- target_type
- target_id
- request_id
- limit (1–500)
- offset (>= 0)

Results are newest-first using `created_at DESC, id DESC`.

## Security and tenant isolation
Callers must supply an organisation scope when requesting tenant audit history.
The service does not expose an organisation-wide unfiltered tenant shortcut;
filtering is explicit and server-side.

## Request correlation
`request_id` provides correlation between a request and the audit events generated
during its processing.

## Future extension points
This phase intentionally does not introduce:
- audit editing
- audit deletion
- full event bus infrastructure
- external log streaming
- analytics/reporting read models
- retention/purge policy

Those can be added through later Core extension points without changing the
authority model.
