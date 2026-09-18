# Phoenix Core V2 — Architecture Authority

## Status

Authoritative Phoenix Core V2 architecture.

## Core Authority

Phoenix Core V2 is the single authoritative Phoenix Core/Foundation.

V1 is retained as reference and migration material only.

> V1 is the teacher; V2 is the new system.

## Phoenix Boundaries

Phoenix Core owns platform-wide foundational capabilities.

Phoenix System provides system administration and commercial control through Core.

Phoenix Platform provides the generic presentation and orchestration experience.

Business modules own their domain capabilities and data.

## Data Authority

Every domain has one authoritative owner.

Core owns Core data.

Business modules own business-domain data.

Inventory owns the authoritative Item Master for physical and commercial items.

No competing master or duplicate authority may be introduced.

## Tenant Isolation

Tenant isolation is mandatory.

A tenant must never be able to access another tenant's data through:

- APIs
- modules
- searches
- reports
- files
- background jobs
- integrations
- notifications
- caches
- exports

## Security

All access is through controlled server-side APIs and application services.

Clients and modules must never access Core persistence directly.

Authentication, identity, membership, authorization and entitlement are separate concerns.

## Module Architecture

Modules are independently extensible and versioned.

Core provides foundational capabilities and contracts without owning business-domain entities.

## Architecture Evolution

Architecture is a living record.

Architecture Decision Records preserve the history of important decisions.

When a decision changes, the previous decision is preserved and a new decision supersedes it.

Architecture should evolve deliberately, never blindly.
