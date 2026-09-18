# ADR-038 — Phoenix System Framework Architecture

- Status: Accepted
- Date: 2026-09-03
- Decision: Establish Phoenix System as the generic administrative application layer above Phoenix Core V2 and the Generic Framework.

## Context

Phoenix Core V2 is the authoritative foundation for identity, organisations, memberships, permissions, entitlements, sessions, audit, configuration, APIs, jobs, AI, and security.

The Phoenix Generic Framework provides reusable application-level contracts, context, module integration, navigation, capabilities, and orchestration.

Phoenix requires a generic System administration experience for administering the Phoenix platform and its tenant/company environments.

## Decision

Phoenix System is an application-level administrative layer built on Phoenix Core V2 and the Phoenix Generic Framework.

Phoenix System does not create competing authority for:

- Identity
- Users
- Organisations
- Memberships
- Roles
- Permissions
- Licensing
- Entitlements
- Modules
- Sessions
- Audit
- Security

Those remain authoritative in Phoenix Core.

## Dependency Direction

The dependency direction is:

Phoenix Core
    ?
Phoenix Generic Framework
    ?
Phoenix System Framework
    ?
Phoenix Platform UI

Business modules remain separate from System and do not become dependencies of generic System administration.

## System Responsibilities

Phoenix System provides reusable administrative orchestration for:

- Company administration
- User administration
- Membership administration
- Role and permission administration
- Module administration
- Entitlement administration
- System configuration access
- Platform administration workflows
- Administrative navigation

System operations must execute through authoritative Core services/contracts.

## Company Administration

Phoenix System may present and orchestrate company administration.

The authoritative company/tenant records remain owned by Phoenix Core.

System must not maintain a duplicate company master.

## User Administration

Phoenix System may provide user administration experiences.

Identity, authentication, memberships, roles, and permissions remain authoritative in Core.

System must not maintain a duplicate user or identity store.

## Module Administration

Phoenix System may present and administer registered modules.

Core remains authoritative for module registration and entitlements.

System must not create a competing module registry.

## Licensing and Entitlements

System may provide the administrative experience for licensing and entitlement operations.

Core remains authoritative for entitlement state and enforcement.

## Security

System operations must execute within authenticated Core security context.

Administrative actions must preserve:

- Identity
- Organisation context
- Permissions
- Entitlements
- Session security
- Audit requirements

System must not bypass Core authorization.

## Persistence

Phoenix System should not introduce persistence where Core already owns the authoritative data.

Any future System-owned persistence requires an explicit architectural decision establishing why the data is genuinely System-owned.

## UI Boundary

Phoenix System is not itself the final presentation layer.

The Platform UI consumes System contracts and services to render administrative experiences.

## Module Boundary

System administration is generic platform functionality.

Business-specific administration belongs to the owning business module.

## Extensibility

Phoenix System must be extensible through contracts and service boundaries.

New generic administrative capabilities should extend System without creating another administrative authority.

## Architecture Enforcement

Tests must prevent:

- Duplicate identity authority
- Duplicate organisation authority
- Duplicate permission authority
- Duplicate licensing authority
- Duplicate module registry authority
- Direct database access from System presentation code
- Business-module dependencies inside generic System services
- Core depending on System

## Consequences

Phoenix gains a reusable administrative experience that can support multiple companies, users, modules, and future business applications while preserving one Core authority.

System can evolve independently from individual business modules while remaining constrained by Core authority and Generic Framework contracts.

## Supersession

This ADR supersedes no previous architectural decision.

It extends ADR-037 and the established Phoenix Core V2 architecture.
