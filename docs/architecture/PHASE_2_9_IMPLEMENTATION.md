# Phase 2.9 — Files, Documents & Attachments Foundation

## Purpose
Phoenix Core provides a generic, tenant-scoped foundation for files, documents and attachments used by Phoenix platform capabilities and business modules.

## Boundary
Files and document infrastructure are Core platform capabilities. Business modules own the business meaning and context of a document, while Core owns file metadata, storage abstraction, lifecycle, access enforcement and attachment relationships.

## Authority
Phoenix Core is the authoritative authority for document/file metadata, ownership, tenant scope, access control and storage contracts.

Modules must not access Core file storage directly and must not create competing file/document authorities.

## Business Context
Documents may carry a generic context_type and context_id so CRM, Projects, Sales, Production, Inventory, Accounts and future modules can associate files without Core depending on those domains.

## Storage
Core exposes a storage abstraction rather than coupling the domain to a specific storage provider.

Development may use local filesystem storage. Future deployments may use object storage or another provider without requiring business modules to change.

## Security
All document operations are tenant-scoped and server-side authorized.

A document belonging to one organisation must never be readable, writable, downloadable, or attachable by another organisation.

## Lifecycle
Files have an explicit lifecycle and are not silently deleted.

The foundation supports future document versioning without requiring modules to implement their own versioning systems.

## Attachments
Attachments are relationships between a Core document/file and a generic business context.

The same Core document authority may support attachments to different supported contexts without Core depending on business-module tables.

## Audit
Security-sensitive document operations are auditable through the existing Core audit service.

## Database
Phase 2.9 uses the existing authoritative Phoenix Core database.

No second document/file database is introduced.

## Extensibility
Storage providers, document processing, previews, virus scanning, retention policies and external object storage can be added through defined extension points without changing Core ownership.
