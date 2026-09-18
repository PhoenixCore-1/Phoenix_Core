# ADR-037 — Phoenix Generic Framework Architecture

- Status: Accepted
- Date: 2026-09-03
- Decision: Establish the Phoenix Generic Framework as the reusable product layer above Phoenix Core V2.

## Context

Phoenix Core V2 is the authoritative Phoenix foundation. It owns platform authority such as identity, organisations, memberships, permissions, entitlements, sessions, audit, configuration, APIs, jobs, AI, and security.

Phoenix requires a reusable product layer that provides common System, Company, User, Module, Navigation, and Platform experiences without creating a second Core or competing authority.

The Framework must support future Phoenix business modules without requiring Core to be rebuilt for each module.

## Decision

Phoenix Generic Framework is a distinct product layer above Phoenix Core V2.

The Framework consumes authoritative Core services and contracts. Core never depends on the Framework.

The Framework provides reusable application-level contracts and orchestration for:

- System administration
- Company/tenant experience
- User experience
- Module experience
- Navigation
- Platform capabilities
- Common application presentation/orchestration

The Framework does not become an authority for identity, tenancy, permissions, licensing, audit, security, AI, jobs, or other capabilities already owned by Core.

## Authority Boundary

The authoritative dependency direction is:

Phoenix Core
    ?
Phoenix Generic Framework
    ?
Phoenix Platform UI
    ?
Business Modules

The dependency direction must never be reversed.

Business modules may consume Framework capabilities where appropriate, but they must not bypass Core authority.

## Core Responsibilities

Core remains authoritative for:

- Identity
- Organisations and tenant isolation
- Memberships
- Roles and permissions
- Sessions and authentication
- Licensing and entitlements
- Module registry authority
- Audit
- Configuration
- API and integration boundaries
- Background jobs
- AI platform capability
- Security controls

## Framework Responsibilities

The Generic Framework provides reusable application-level capabilities including:

- Company administration experience
- User administration experience
- System administration orchestration
- Common module presentation contracts
- Navigation registration contracts
- Platform context contracts
- Common application service contracts
- Extension points for future Phoenix capabilities

The Framework may orchestrate Core capabilities but must not duplicate their authoritative storage or rules.

## Module Boundary

Business modules remain independently extensible.

A module owns its business domain, business rules, workflows, domain data, and domain-specific intelligence.

Modules consume:

- Core authority
- Framework contracts
- Platform UI capabilities

Modules must not create competing Core authorities.

## UI Boundary

Phoenix Platform UI is a presentation/orchestration layer.

UI clients must communicate through application/API boundaries and must never directly access Core databases or module databases.

## Contract Principle

Framework contracts define stable interfaces between the reusable Phoenix product layer and implementations.

Contracts must remain provider-independent and domain-neutral where the capability is generic.

Business-specific meaning belongs to the owning module.

## Extension Principle

The Framework must be extensible through defined contracts and registration points.

Adding a new generic platform capability must not require creating a competing Framework or Core.

Adding a business capability must normally be implemented as a module rather than modifying the Framework.

## Persistence Principle

The Framework must not introduce duplicate authoritative masters.

Where Core already owns authoritative data, Framework services consume Core authority.

Framework-owned persistence may only be introduced where the Framework has a clearly defined application-level responsibility that is not already authoritative elsewhere.

## Security Principle

Framework operations execute within authenticated and authorised Core security context.

The Framework must preserve:

- Identity context
- Organisation/tenant context
- Permissions
- Entitlements
- Audit requirements
- Session/security boundaries

The Framework must never bypass Core security.

## Architecture Enforcement

Architecture tests must prevent:

- Core importing Phoenix Framework
- Direct database access from Framework presentation code
- Duplicate identity/tenant/permission/licensing authorities
- Business-module dependencies inside generic Framework contracts
- Provider-specific implementations leaking into generic contracts
- Circular dependencies between Core and Framework

## Filesystem Boundary

Phoenix Core remains under:

`src/phoenix_core/`

The Generic Framework is under:

`src/phoenix_framework/`

They are separate packages with a one-directional dependency from Framework to Core.

## Consequences

This creates a reusable Phoenix product layer that can support multiple business modules and future Phoenix applications while preserving one Core authority.

The Framework can evolve independently from individual business modules while remaining constrained by Core authority and stable contracts.

## Supersession

This ADR supersedes no previous architectural decision.

It extends the established Phoenix Core V2 authority, module, API, security, licensing, and extensibility decisions.

Future changes must be recorded as new ADRs or amendments/superseding ADRs rather than silently replacing this decision.
