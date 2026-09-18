# Phoenix Company Platform — Hardening Audit V1

**Status:** In progress / hardening gate
**Branch:** `feature/core-http-api-v1`
**Date:** 2026-09-14

## Scope

This audit verifies the Company Platform against the locked Phoenix architecture:

- Phoenix Core remains the sole identity, tenant, permission, entitlement and audit authority.
- Company Platform remains tenant-level administration and oversight, not a second Phoenix control plane.
- HTTP transport does not become a persistence or business authority.
- Company Platform regulatory/compliance behavior must consume the appropriate System Platform/Core legal framework rather than create a competing authority.

## Findings and actions completed

### 1. Authentication and tenant context — PASS

Browser authentication uses the Core session cookie and request context is resolved server-side. The browser does not supply authoritative identity, organisation, permissions or entitlements.

### 2. Company mutation authorization — PASS

People & Access mutations require Company Platform permissions and validate the target membership, role or user against the current organisation before mutation.

### 3. Company activity — PASS

Activity is sourced from the Core Audit service and is tenant-scoped through the resolved request context. Identity filters are additionally checked against memberships in the current organisation.

### 4. Company reports — HARDENED

Reports are explicitly scoped to Company Administration and are now routed through a Company Platform application-service boundary rather than implementing reporting logic in the HTTP adapter.

### 5. Company workspaces — HARDENED

Workspace HTTP routes no longer construct the workspace service or record audit events directly in the transport adapter. Workspace behavior is behind the Company Platform application-service boundary.

### 6. Company Platform read authorization — HARDENED

People & Access read surfaces now require the relevant Company Platform administration permission. This prevents an authenticated ordinary tenant member from enumerating company users, memberships, roles and permissions merely because they have a valid session.

### 7. Migration bootstrap — HARDENED

A central migration runner now applies every checked-in SQL migration in deterministic filename order for the development HTTP application. Company Platform workspace and visibility migrations, plus the Company Platform permission migration, are therefore included in a fresh development database.

A missing `011_company_platform_permissions.sql` migration was restored with the eight authoritative Company Platform permissions.

## Regulatory / Legal boundary

The Company Platform must use the Phoenix legal/policy foundation already owned by Core and the System Platform framework. It must not create a second legal document, acceptance, audit, identity or regulatory authority.

The existing Core legal ADR explicitly establishes Core as authoritative for platform policy state, acceptance records, enforcement state and audit integration, while legal content remains controlled by the appropriate legal/commercial authority.

Broader ERP/SARS/tax compliance must not be introduced into the V2.0 Core merely as part of Company Platform hardening. If the System Platform regulatory framework is expanded, Company Platform should consume its published requirements and manage company-level applicability, obligations, evidence and status through the approved Core contracts.

## Remaining hardening gates

These are deliberately not marked complete until verified in code and tests:

1. **Company Settings** — tenant identity/configuration, departments, lead times, freight configuration, contacts and company defaults, without platform licensing/module control.
2. **Company Compliance & Legal HTTP/application surface** — company obligations, applicability, contracts, evidence, status and expiry, connected to the authoritative legal/regulatory framework.
3. **Atomic company user provisioning** — create user + membership as one Core transaction/workflow, or compensate cleanly if membership creation fails.
4. **CSRF protection** — the secure session cookie uses `HttpOnly`, `Secure` and `SameSite=Lax`; state-changing browser requests still need an explicit CSRF strategy before production exposure.
5. **Typed HTTP request models** — replace raw `request.json()` mutation payloads with Pydantic models and standard FastAPI validation responses.
6. **Core application boundary consolidation** — remaining Company Platform read routes that call `core_service` directly should be progressively moved behind CoreApi/application-service methods.
7. **Automated execution** — the new and existing Company Platform HTTP tests must be executed against the actual branch. No passing count is claimed until the suite has been run.
8. **End-to-end browser flow** — login → Core session → Company Platform → tenant context → authorization → workspace must be verified against the actual frontend.

## Gate decision

**Company Platform is not yet declared fully locked.**

The major boundary defects found during this audit have been corrected, but Company Settings, Company Compliance & Legal integration, production CSRF protection, and actual test execution remain release gates.
