# Phase 2.4 — Authentication & Session Management

Phase 2.4 adds the Core authentication/session application boundary on top of
Identity, Organisations/Memberships, Roles and Permissions.

## Scope
- Credential authentication.
- Organisation membership validation during organisation-scoped login.
- Active session creation.
- Session revocation and expiry enforcement.
- Revoke-all sessions for a user.
- Password change with current-password verification.
- Password minimum length validation.

## Security boundary
Authentication establishes identity and session state. Organisation membership
remains the authority for organisation context. Authorization remains a separate
capability and must not be bypassed by authentication.

## Out of scope
MFA, external identity providers, API keys, device management, rate limiting,
refresh-token rotation and production password policy tuning are future Core
extension points.
