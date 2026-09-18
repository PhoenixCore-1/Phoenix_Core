# Phoenix Core V2 — Phase 2.7 Implementation

## Purpose
Phase 2.7 establishes Core-owned configuration, runtime settings, and feature flags.

## Authority
Core owns persistence and evaluation. Clients and business modules do not access these tables directly.

## Scope
- Global and organisation-scoped settings.
- Typed setting values: STRING, INTEGER, NUMBER, BOOLEAN, JSON.
- Effective setting resolution: organisation override, otherwise global default.
- Global and organisation-scoped feature flags.
- Feature flag evaluation is server-side and defaults to disabled when no flag exists.
- Organisation-scoped records require an existing ACTIVE organisation.

## Boundaries
Configuration answers what value should be used. Feature flags answer whether a capability is enabled. Permissions answer whether an identity may perform an action. Entitlements answer whether an organisation has access to a module/capability. These authorities remain separate.

## Sensitive values
The generic settings store is not a secrets vault. Secret material must not be placed in generic Core settings. A future secrets provider may be added through a Core extension point.

## Persistence
Migration `002_core_configuration.sql` adds `core_settings` and `feature_flags` to the authoritative V2 database. It is additive and uses `IF NOT EXISTS`.

## Audit
Configuration changes should be auditable through the existing Core audit contract. Phase 2.7 does not duplicate audit persistence.
