# Phoenix Core V2 — Phase 1 Implementation

## Current vertical slice

The first implementation slice establishes:

- Identity
- Human user
- Organisation
- Organisation membership
- Organisation roles
- Role assignment
- Permissions
- Sessions
- Password authentication
- Basic authorization evaluation
- Technical module/entitlement schema foundation
- Audit events
- SQLite persistence
- Initial architecture tests

## Authority rules

Core V2 owns the foundational entities above.

Business modules must not be added to Core persistence.

Inventory remains the authoritative Item Master.

## Persistence

The first implementation uses SQLite for local development.

The logical authority is independent of the eventual production database topology.

Local runtime databases are excluded from Git.

## Security

Passwords use standard-library scrypt hashing.

Sessions store only token hashes.

Tenant membership is explicit.

Role assignment validates that membership and role belong to the same organisation.

## Next implementation increments

1. Formal repository/unit-of-work ports.
2. API boundary and request/response contracts.
3. Module registry and entitlement application services.
4. Complete authorization resource checks.
5. MFA extension points.
6. Migration/version management.
7. Integration/contract tests.
8. Production-grade API implementation.
