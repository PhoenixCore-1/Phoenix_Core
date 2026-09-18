# Phase 2.10 — Core API & Integration Foundation

## Purpose

Phoenix Core exposes one authoritative API and integration boundary for Phoenix Platform, Phoenix business modules and future external integrations.

## API Authority

Phoenix Core remains the authoritative authority for:

- authentication context
- identity
- organisation/tenant context
- permissions
- entitlements
- Core services
- Core contracts

The API is an access boundary to Core. It is not a second authority.

## Versioning

The public API uses explicit versioning:

`/api/v1/...`

Breaking API changes require a new major API version.

Compatible additions may be introduced within the existing version according to the API compatibility policy.

## Request Context

Every authenticated API operation may carry a standard request context containing:

- request_id
- identity_id
- organisation_id
- session_id

The context is created at the API boundary and passed into application services.

## Tenant Isolation

Organisation context is authoritative and must be enforced server-side.

API clients must never select or override an organisation context beyond organisations to which the authenticated identity is legitimately entitled.

## Security Boundary

API operations must:

1. authenticate the caller
2. establish identity context
3. establish organisation context
4. enforce permissions
5. enforce module entitlements where applicable
6. invoke application services
7. return a controlled API response

API clients must never access the Core database directly.

## Error Contract

API errors use a consistent structured representation containing an error code, human-readable message and request identifier.

Internal implementation details, database errors and sensitive security information must not be exposed to API consumers.

## Integration Boundary

Core provides framework-independent contracts for future integrations.

Potential integration mechanisms include:

- internal module contracts
- REST API
- API keys
- webhooks
- external service adapters

Concrete external integrations must not become Core domain dependencies.

## Audit

Security-sensitive and significant API operations integrate with the existing Core audit foundation.

Request identifiers provide correlation between API activity and audit records.

## Extensibility

The API boundary must remain replaceable at the transport/framework level.

Business modules depend on Core contracts and application services rather than HTTP framework internals.

## Architecture Rule

No API implementation may bypass Core application services to access domain persistence directly.
