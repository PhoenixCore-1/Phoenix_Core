# Phoenix Third-Party & Provenance Register

## Purpose

This register records external software, libraries, frameworks, assets, specifications, code, documentation, and other material intentionally incorporated into Phoenix.

It supports ADR-041: Phoenix IP, Provenance & Clean-Room Development.

The register is part of Phoenix development governance and should be updated when material external to Phoenix is incorporated into an authoritative Phoenix component.

## Rules

1. External material must have a known source.
2. Usage rights or applicable licence must be established before incorporation.
3. Proprietary or confidential material must not be incorporated without appropriate authorization.
4. General industry knowledge and standard engineering patterns do not require registration as third-party material.
5. Open-source and third-party components should be recorded with their applicable licence.
6. AI-assisted output remains subject to ADR-041.
7. If provenance is uncertain, the material must not become part of an authoritative Phoenix release until reviewed.
8. This register does not replace legal review where legal review is required.

## Register

| ID | Component / Material | Version | Type | Source | Licence / Usage Right | Phoenix Use | Introduced | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| P-0001 | Python | 3.13 | Runtime | Python Software Foundation | Python Software Foundation Licence | Application runtime | 2026-09-04 | REVIEWED | Confirm exact deployed version before release |
| P-0002 | SQLite | Current supported runtime version | Database engine | SQLite Project | Public domain | Core persistence engine | 2026-09-04 | REVIEWED | Confirm deployed runtime version before release |

## Phoenix-Originated Material

Phoenix-specific source code, architecture, database migrations, domain models, services, tests, documentation, and business implementation developed from Phoenix requirements are considered Phoenix-originated unless an external source is explicitly recorded above or otherwise documented.

## Review Status Definitions

### REVIEWED

Source and applicable usage rights have been identified and no known incorporation restriction prevents the intended Phoenix use.

### PENDING

Material has been identified but provenance, licence, or intended usage still requires confirmation.

### EXCLUDED

Material was reviewed and intentionally not incorporated into Phoenix.

## Release Requirement

Before a production release, material dependencies and externally sourced assets materially included in the release should have an identifiable provenance and applicable usage right.

The register should remain under version control with the Phoenix repository.
