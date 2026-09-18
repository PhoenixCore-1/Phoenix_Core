# Phoenix Core V2 — Phase 2.5 Implementation

## Module Registry and Organisation Entitlements

Phase 2.5 operationalises the Core module registry and technical organisation/module entitlement layer.

### Implemented

- Module registration, lookup and listing.
- Module lifecycle: `REGISTERED`, `ENABLED`, `DISABLED`, `RETIRED`.
- Explicit module lifecycle transition rules.
- Organisation/module entitlement grant, lookup and listing.
- Entitlement lifecycle: `ACTIVE`, `SUSPENDED`, `REVOKED`.
- Retired modules cannot receive new entitlements.
- Entitlements require an active organisation.
- Module availability requires all three:
  1. active organisation,
  2. enabled module,
  3. active organisation entitlement.
- Effective capability requires both module availability and the existing Core permission authorization.
- Cross-tenant capability checks remain denied.

### Authority boundary

Core owns module registry and technical entitlements. Core does not own business-domain records such as customers, items, quotes, sales orders, projects, production orders or invoices.

A module must not decide licensing independently. It consumes Core capability/entitlement results.

### Not included

- Billing/invoicing implementation.
- Subscription plans.
- Usage metering.
- External licensing providers.
- Module installation/update packaging.
- API/UI implementation.
- Module-specific business permissions beyond the existing Core RBAC mechanism.

## Verification target

Phase 2.5 adds eight tests and must retain all existing Phase 2.1–2.4 tests.
