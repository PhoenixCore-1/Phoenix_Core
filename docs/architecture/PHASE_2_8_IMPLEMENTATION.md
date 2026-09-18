# Phase 2.8 — Internal Communications & Collaboration Foundation

## Purpose
Phoenix Core provides a generic internal collaboration foundation for tenant-scoped channels, direct/group collaboration, messages, threads, reactions, read state and presence.

## Boundary
Communications is an internal Phoenix platform capability. External customer communications such as WhatsApp, customer email and call history remain CRM-owned capabilities.

## Authority
Core owns communication identity, organisation scope, channel membership, message persistence and access enforcement. Modules do not access communications tables directly; they consume Core contracts.

## Business context
Messages may carry a generic `context_type` and `context_id` so Projects, CRM, Production and other modules can attach business context without Core depending on those domains.

## Security
All channel reads/writes require active organisation membership and channel membership. Tenant identity is validated server-side. Cross-tenant access is denied.

## Extensibility
The persistence model deliberately leaves transport/realtime delivery outside the domain service. Future WebSocket/realtime infrastructure can consume these Core contracts without changing the domain ownership model.

## Database
Migration `003_core_communications.sql` is additive and uses the existing authoritative Core database. No second communication database is introduced.
