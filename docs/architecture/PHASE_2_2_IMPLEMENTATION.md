# Phoenix Core V2 — Phase 2.2 Implementation

Phase 2.2 implements the Core organisation/tenant and membership lifecycle on top of the Phase 1 foundation and Phase 2.1 identity/user foundation.

## Implemented

- Organisation read/update lifecycle.
- Organisation states: `ACTIVE`, `SUSPENDED`, `CLOSED`.
- Closed organisations are terminal.
- Membership read/list lifecycle.
- Membership states: `ACTIVE`, `SUSPENDED`, `REMOVED`.
- Removed memberships are terminal; restoration creates a new membership after the existing membership is removed.
- New memberships are allowed only for active organisations.
- Organisation suspension/closure suspends active memberships without changing the global identity state.
- A membership can only be reactivated when both its organisation and identity are active.
- Identity may belong to multiple organisations through separate memberships.
- Effective authorization now requires an active organisation as well as an active membership and role.
- Existing unique `(identity_id, organisation_id)` constraint remains the authoritative duplicate-membership protection.

## Tenant boundary rule

Organisation context is server-side authority. Membership records are explicitly scoped to an organisation. Core authorization will not grant permissions from a suspended/closed organisation.

## Validation

Phase 2.2 adds six focused tests covering organisation lifecycle, membership lifecycle, duplicate memberships, suspended-organisation behaviour, multi-organisation identity membership, and terminal removal.
