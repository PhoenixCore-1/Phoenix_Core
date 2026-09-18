# Phoenix Core V2 — Phase 2.1

## Identity & User Foundation

Phase 2.1 strengthens the Core identity/user slice without introducing business-domain ownership.

Implemented:
- Read identity and user records through application services.
- Update user username/display name with validation and uniqueness enforcement.
- User lifecycle: ACTIVE, SUSPENDED, DISABLED.
- User lifecycle changes synchronise the authoritative identity status.
- Non-active lifecycle transitions revoke active sessions.
- UUID role-assignment identifiers for consistency.
- Automated tests for lifecycle, update, uniqueness and validation.

Identity remains the foundational principal. User is the human-facing representation attached to an identity. Organisation membership remains the tenant boundary and is intentionally not duplicated here.
