# ADR 034 — Phoenix Core Files, Documents & Attachments Authority

## Status
Accepted

## Decision
Phoenix Core will provide the authoritative generic foundation for files, documents and attachments across Phoenix.

Core owns:
- file/document metadata
- tenant ownership
- access enforcement
- lifecycle
- storage abstraction
- attachment relationships
- audit integration

Business modules own the business meaning and context of documents but do not create competing document/file authorities.

## Rationale
A single Core document authority prevents CRM, Projects, Production, Sales, Inventory and other modules from developing incompatible storage, security, lifecycle and attachment models.

## Storage Boundary
The Core domain will depend on a storage contract rather than a concrete storage provider.

This allows local development storage to be replaced by object/cloud storage without changing business-module contracts.

## Consequences
- One authoritative document/file model.
- Strict tenant isolation.
- Modules interact through Core contracts/services.
- Storage implementation remains replaceable.
- Future processing, previews, scanning and retention capabilities can be added without changing ownership.
