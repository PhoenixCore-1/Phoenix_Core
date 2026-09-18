# ADR 035 — Phoenix Core API & Integration Authority

## Status

Accepted

## Decision

Phoenix Core will expose one authoritative API and integration boundary for Phoenix Platform, business modules and future external integrations.

The API is an access boundary to Core and does not create a second business or data authority.

## API Versioning

The API will use explicit versioned paths beginning with:

`/api/v1/...`

Breaking contract changes require a new major API version.

## Request Context

API requests establish a standard request context containing identity, organisation/tenant, session and request correlation information.

## Security

API access is authenticated and server-side authorized.

Tenant isolation, permissions and module entitlements remain Core responsibilities.

## Persistence Boundary

API implementations must not access Core database persistence directly.

API requests must invoke Core application services and contracts.

## Integration

Core exposes framework-independent integration contracts.

Concrete transport and external integration implementations remain replaceable and must not become Core domain dependencies.

## Rationale

A single API boundary prevents Phoenix Platform, business modules and external systems from developing competing authentication, tenant, authorization and persistence paths.

## Consequences

- One authoritative Core API boundary.
- Explicit API versioning.
- Standard request context.
- Consistent error handling.
- Strong tenant/security enforcement.
- Framework-independent Core contracts.
- Replaceable transport implementations.
- Modules remain decoupled from Core infrastructure.
