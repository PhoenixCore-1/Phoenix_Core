# Phoenix Core HTTP API Surface V1

## Status

Architecture contract defining the target HTTP surface between Phoenix Core and Phoenix client applications. An endpoint listed here is not considered live until implemented by an HTTP adapter and covered by tests.

## Current implementation milestone

The authentication and current-context slice is implemented in the FastAPI transport adapter. The Company Platform People & Access, Workspaces, Data Visibility, Reporting, Settings and Compliance & Legal read-only slices are also implemented against Phoenix Core authority.

These routes resolve identity, organisation, permissions and module entitlements through Core. The browser does not become an authority for any of them.

## Authority

Phoenix Core remains the single authority for authentication, sessions, identity, organisation/tenant context, memberships, roles, permissions, module entitlements, audit evidence, Core documents, and legal/compliance evidence.

The frontend must never become an authority for these concerns.

## Transport boundary

```text
Phoenix Core domain/services
        |
     CoreApi
        |
   HTTP API V1
        |
 Phoenix API Client
        |
    Phoenix React UI
```

HTTP handlers must invoke Core application services/contracts. They must not access Core database tables directly. All versioned routes begin with `/api/v1`.

## Request context

Authenticated requests resolve context server-side from the Core session. The browser must not be trusted to supply authoritative identity, organisation, membership, permission, or entitlement values. Each request carries a request/correlation ID so API responses and audit events can be connected.

## Standard response contract

Successful responses use the Core `ApiResponse` contract:

```json
{"data": {}, "request_id": "..."}
```

Errors use the Core `ApiError` contract:

```json
{"code": "AUTHORIZATION_ERROR", "message": "Permission denied.", "request_id": "..."}
```

## Authentication and session

| Method | Route | Purpose | State |
|---|---|---|---|
| POST | `/api/v1/auth/login` | Authenticate user and establish Core session | IMPLEMENTED |
| POST | `/api/v1/auth/logout` | Revoke current session | IMPLEMENTED |
| GET | `/api/v1/auth/session` | Return current session state | IMPLEMENTED |

## Current context

| Method | Route | Purpose | State |
|---|---|---|---|
| GET | `/api/v1/me` | Current authenticated user context | IMPLEMENTED |
| GET | `/api/v1/me/identity` | Current Core identity | IMPLEMENTED |
| GET | `/api/v1/me/organisation` | Current organisation | IMPLEMENTED |
| GET | `/api/v1/me/permissions` | Effective permissions | IMPLEMENTED |
| GET | `/api/v1/me/entitlements` | Effective module entitlements | IMPLEMENTED |

## Memberships, roles and permissions

The Company Platform People & Access surface is implemented, including tenant-bound mutations, server-side authorization and Core audit recording.

```text
GET/POST/PATCH /api/v1/company/users
GET /api/v1/company/memberships
GET/POST/PATCH /api/v1/company/roles
POST /api/v1/company/memberships/{id}/suspend
POST /api/v1/company/memberships/{id}/restore
POST /api/v1/company/memberships/{id}/remove
GET /api/v1/company/permissions
GET /api/v1/company/roles/{id}/permissions
POST/DELETE /api/v1/company/roles/{id}/permissions/{permission_id}
POST/DELETE /api/v1/company/memberships/{id}/roles/{role_id}
```

## Company Platform

Company Platform is tenant/company administration and cannot become a second platform control plane.

```text
GET /api/v1/company
GET /api/v1/company/workspaces
GET /api/v1/company/visibility
GET /api/v1/company/activity
GET /api/v1/company/reports
GET /api/v1/company/settings
GET /api/v1/company/compliance
```

Company context is derived through Core request context and membership validation.

### Compliance & Legal

`GET /api/v1/company/compliance` exposes the existing Core policy, active policy-version and policy-acceptance records for the authenticated company context. It reports active requirements, current identity acceptance status and acceptance counts without creating a second legal/evidence authority.

Company contracts and dedicated evidence-record management remain intentionally unimplemented until authoritative Core models and workflows exist. The UI must not imply those capabilities are live.

## System Platform

System Platform owns Phoenix-wide regulatory/legal framework, platform settings, licensing, module activation and other platform-control concerns. Company Platform cannot perform those operations.

## User Platform

User Platform is the personal workspace and does not replace Core identity/security authority.

## Documents

Core remains the document and document-version authority. Legal evidence references exact document versions and hashes.

## Legal and compliance

The existing Core legal foundation contains policies, policy versions and policy acceptances. Legal actions are server-side operations. A browser checkbox or client-side state is never the legal evidence authority. Completion must resolve authenticated identity and organisation context from Core and associate the exact legal requirement/document version with immutable evidence and the corresponding Core audit event.

## Audit

Audit records are append-only Core evidence. Ordinary application clients cannot modify or delete audit events.

## Definition of done

1. Every implemented route is backed by an authoritative Core service.
2. Every authenticated route resolves Core request context server-side.
3. Permission and entitlement checks occur server-side.
4. Tenant isolation is enforced by Core/application services.
5. API errors use the Core error contract.
6. Request IDs propagate through the API and audit boundary.
7. Mutations produce appropriate audit evidence.
8. HTTP routes do not access persistence directly.
9. Browser authentication does not require a second authority.
10. React can operate entirely through the documented API boundary.
