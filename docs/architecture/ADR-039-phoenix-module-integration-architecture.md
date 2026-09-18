# ADR-039 — Phoenix Module Integration Architecture

- Status: Accepted
- Date: 2026-09-04
- Decision: Phoenix Core V2
- Supersedes: None

## 1. Context

Phoenix Core V2 is designed as a single authoritative platform foundation with independently extensible business modules.

The Generic Phoenix Framework already provides module discovery, lifecycle, navigation, capabilities and framework orchestration. Phoenix Core already provides authoritative identity, organisation/tenant context, permissions, entitlements, security, audit, API/integration infrastructure, background jobs and AI services.

A formal architecture is now required to define how:

- Modules communicate with Phoenix Core.
- Modules communicate with the Generic Phoenix Framework.
- Modules communicate with other modules.
- Synchronous and asynchronous communication operate.
- Tenant, identity, security, authorization and entitlement context is propagated.
- Module dependencies and capabilities are declared and discovered.
- Module data ownership is preserved.
- Integration contracts evolve without requiring Core or all modules to be rebuilt.
- Failures, retries and duplicate operations are handled safely.
- Modules can eventually operate across distributed deployments without changing their business contracts.

This architecture must prevent modules from becoming tightly coupled to Core internals, other module databases or implementation details.

## 2. Decision

Phoenix V2 will use a contract-based module integration architecture.

The architectural dependency direction is:

Phoenix Core
    ↓
Phoenix Generic Framework
    ↓
Module Integration Contracts
    ↓
Business Modules

Modules may communicate with other modules only through explicit published contracts or asynchronous events/messages.

Modules must never communicate by directly accessing another module's database, persistence implementation or private internal classes.

## 3. Core Authority

Phoenix Core remains authoritative for platform-wide concerns, including:

- Identity
- Organisations and tenant context
- Memberships
- Authentication and sessions
- Authorization and permissions
- Licensing and entitlements
- Security
- Audit
- Configuration
- Core API/integration boundary
- Background jobs
- AI platform services
- Other approved Core platform capabilities

Modules consume these services through approved contracts.

Modules must not create duplicate authorities for these concerns.

## 4. Generic Framework Authority

The Generic Phoenix Framework remains responsible for reusable application-level orchestration and presentation-facing contracts, including:

- Module discovery
- Module lifecycle integration
- Navigation registration
- Platform capability registration
- Framework context
- Framework-level orchestration

The existing ModuleContract and ModuleRegistry remain the authoritative Framework mechanisms for generic module registration and discovery.

Phase 3.3 must extend this architecture rather than replace or duplicate it.

## 5. Module Domain Authority

Each business module owns its own domain model and domain data.

Examples:

- CRM owns customer relationship/domain data.
- Sales owns sales transactions and sales-domain data.
- Inventory owns the authoritative Item Master and inventory-domain data.
- Manufacturing owns manufacturing orders, stages and manufacturing-domain data.
- Accounts owns accounting and financial-domain data.

Other modules may reference domain information through published contracts, identifiers and approved queries/services.

A module must never directly read or write another module's database tables.

## 6. Module-to-Core Communication

Modules communicate with Core through stable Core service contracts and integration boundaries.

The existing CoreIntegrationContract and CoreIntegrationService remain the Core integration boundary.

The Core integration layer must not become a giant dispatcher containing business-module logic.

Core exposes platform capabilities; business modules retain business ownership.

The existing IntegrationRequest and IntegrationResponse provide a foundation for Core-bound integration and must be reused where appropriate.

## 7. Module-to-Framework Communication

Modules integrate with the Generic Framework through defined Framework contracts.

Modules may register or expose:

- Module identity and lifecycle
- Navigation
- Capabilities
- Permissions
- Entitlements
- Approved integration metadata

Framework orchestration must not become a business-domain authority.

## 8. Module-to-Module Communication

Module-to-module communication is a first-class Phoenix architecture capability.

Two communication mechanisms are supported:

### 8.1 Synchronous communication

A module may invoke another module through an explicit published service or contract.

Example:

Sales → CRM Customer Contract

Sales does not import CRM's internal implementation or access CRM persistence directly.

Synchronous communication is appropriate when the caller requires an immediate response.

### 8.2 Asynchronous communication

Modules may publish and consume domain events or messages through Phoenix event infrastructure.

Example:

Sales
    ↓
OrderCreated
    ↓
Phoenix Event Infrastructure
    ├── Inventory
    ├── Manufacturing
    ├── Accounts
    └── CRM

Consumers must not assume that event delivery is instantaneous.

Event handling must support safe retries and idempotent processing.

## 9. Commands, Queries and Events

Phoenix module integration distinguishes:

### Commands

Requests to perform an operation or change state.

Examples:

- CreateCustomer
- CreateSalesOrder
- ReserveInventory
- ReleaseManufacturingOrder

Commands have an owning authority. The owning module validates and executes the business operation.

### Queries

Requests for information without changing state.

Queries must respect tenant, authorization and domain ownership boundaries.

### Events

Notifications that a significant domain event has occurred.

Events represent facts and must not become hidden commands.

An event consumer may react to an event, but the publishing module remains authoritative for the fact it owns.

## 10. Tenant and Security Propagation

Every module integration operation must preserve the originating security context.

At minimum, approved integration context must support:

- Request correlation
- Organisation/tenant identity
- Identity/user context where applicable
- Authentication state
- Authorization
- Entitlement state
- Audit context

A module must never be able to use an integration mechanism to bypass Core security.

Tenant A must never access tenant B through module-to-module communication, events, jobs, queries or commands.

## 11. Authorization and Entitlements

Integration access must be authorized before execution.

The general flow is:

Calling Module
    ↓
Tenant / Security Context
    ↓
Authorization
    ↓
Entitlement
    ↓
Target Contract
    ↓
Business Operation
    ↓
Audit

A module may not treat possession of another module's contract as permission to execute it.

## 12. Audit and Observability

Cross-module operations must remain traceable.

Integration operations should support:

- Request correlation
- Source module
- Target module
- Operation/contract identifier
- Tenant context
- Initiating identity where applicable
- Success/failure
- Relevant audit information

Existing Core audit infrastructure remains authoritative.

Modules must not create competing global audit authorities.

## 13. Dependencies

Modules must explicitly declare integration dependencies.

Dependencies must identify:

- Required module
- Optional module where applicable
- Required capability or contract
- Compatible version/range
- Dependency purpose

Dependency resolution must occur through the module/framework integration architecture.

Circular module dependencies must be detected and prevented.

Example of a prohibited dependency chain:

CRM → Sales → CRM

unless a future architecture explicitly introduces an independent intermediary contract/event boundary that removes the circular dependency.

## 14. Capability Discovery

Modules may publish capabilities that other modules can discover.

Capability discovery must distinguish:

- Module exists
- Module is enabled
- Module is entitled
- Capability is available
- Calling party is authorized

Capability discovery must not bypass Core entitlement or authorization.

## 15. Versioning and Compatibility

Integration contracts are public architectural interfaces.

They must evolve independently from internal implementations.

Breaking changes require explicit versioning and compatibility handling.

Modules must not depend on another module's private classes, database schema or internal implementation.

Contract compatibility must be testable.

## 16. Failure, Retry and Idempotency

Integration architecture must assume that communication can fail.

Synchronous operations must return explicit success/failure information appropriate to the contract.

Asynchronous processing must support:

- Retry
- Idempotency
- Correlation
- Failure tracking
- Safe reprocessing
- Dead-letter or equivalent failure handling where required

Existing Core Job infrastructure, including JobRequest and idempotency support, should be reused rather than duplicated.

Business operations remain responsible for maintaining their own domain consistency.

## 17. Transactions and Consistency

A transaction owned by one module must not silently become a distributed database transaction across multiple modules.

Cross-module consistency should normally use:

- Explicit synchronous contracts
- Domain events
- Background jobs
- Idempotent processing
- Reconciliation where required

Each module remains responsible for the consistency of its own domain.

## 18. Events and Jobs

Phoenix does not currently have a dedicated Core event implementation.

Phase 3.3 will therefore define the event contract and event infrastructure deliberately.

The event architecture must reuse the existing Core asynchronous job infrastructure where appropriate rather than creating a competing background execution authority.

Events and jobs remain distinct concepts:

- Event = a fact that occurred.
- Job = work that must be executed.

A future implementation may use jobs to deliver or process events, but this does not make an event a job.

## 19. Installation and Activation

Module installation and activation must integrate with the existing Core and Framework module lifecycle.

Activation must consider:

- Registration
- Version
- Dependencies
- Required capabilities
- Permissions
- Entitlements
- Configuration
- Compatibility

A module must not require a rebuild of Core to be installed or activated.

## 20. Distributed Deployment Readiness

The integration architecture must not assume that all modules will permanently execute inside the same Python process.

Contracts must therefore avoid depending on:

- Direct object references
- Private imports
- Shared module internals
- Shared database tables

The same logical contracts should be capable of being implemented through local in-process calls initially and service/API or messaging boundaries later.

Distributed deployment is an implementation option, not a requirement for the initial V2 platform.

## 21. Prohibited Patterns

The following are prohibited:

- Direct module-to-module database access.
- Direct SQL access from modules into another module's tables.
- Modules importing another module's private implementation.
- Modules bypassing Core authorization.
- Modules bypassing tenant isolation.
- Duplicate identity, tenant, entitlement or audit authorities.
- Hidden module dependencies.
- Circular dependencies.
- Core containing business-module domain logic.
- A single global integration service containing all business-module operations.
- Events being used as undocumented commands.
- Business modules directly managing provider-specific Core infrastructure.

## 22. Required Phase 3.3 Deliverables

Phase 3.3 will establish, test and document:

1. Module integration contract model.
2. Module dependency contract.
3. Module capability discovery integration.
4. Module-to-Core service contract pattern.
5. Module-to-module synchronous contract pattern.
6. Event contract and event infrastructure.
7. Command and query conventions.
8. Integration context propagation.
9. Authorization and entitlement enforcement.
10. Integration audit/correlation.
11. Version compatibility rules.
12. Retry and idempotency rules.
13. Module lifecycle integration.
14. Circular dependency protection.
15. Architecture-hardening tests.

## 23. Consequences

### Positive

- Business modules remain independently extensible.
- Core remains stable and authoritative.
- Module implementations remain replaceable.
- Cross-module communication becomes explicit and testable.
- Tenant and security boundaries are preserved.
- Future distributed deployment remains possible.
- New modules can be added without rebuilding Core.
- Integration behavior becomes part of the Phoenix architecture rather than being invented separately by each module.

### Negative

- More contracts must be designed before business features are implemented.
- Integration requires additional testing.
- Some simple local operations will have more architectural structure than a direct function call.
- Versioning and dependency management become explicit responsibilities.

These costs are intentional because they prevent the platform from becoming tightly coupled as Phoenix grows.

## 24. Architectural Principle

Phoenix modules are independent business applications operating on a common authoritative platform.

They may communicate, but they do not share ownership.

Core provides the authority.

Framework provides reusable platform orchestration.

Modules provide business capability.

Contracts provide the boundaries.

Events provide decoupled communication.

Tenant and security context follow every boundary.

No module is allowed to become another Core.

## 25. Guiding Principle

V1 is the teacher; V2 is the new system.

The module architecture must be established before business modules are allowed to shape the platform.

## 26. External System Integration and System-of-Record Ownership

Phoenix must support integration with existing customer ERP, WMS and other business systems without requiring customer master data to be uploaded into Phoenix Core.

Phoenix is a hybrid platform.

A customer may:

- Keep an existing ERP/WMS/business system as the system of record for a domain.
- Use Phoenix as the system of record for selected domains.
- Integrate Phoenix with external systems through APIs, connectors, imports/exports or controlled synchronization.
- Use Phoenix read models or synchronized projections where required for application workflows and performance.

For every integrated domain, system-of-record ownership must be explicitly defined.

Phoenix Core remains authoritative for Phoenix platform concerns, including:

- Phoenix identity
- Phoenix organisations/tenants
- Phoenix memberships
- Phoenix authentication and sessions
- Phoenix permissions
- Phoenix entitlements/licensing
- Phoenix security
- Phoenix audit
- Phoenix platform configuration
- Phoenix module lifecycle
- Phoenix platform services

Phoenix Core must not become an implicit master-data authority for customer ERP/WMS domains merely because those systems are integrated with Phoenix.

External systems may therefore remain authoritative for domains such as:

- ERP customer master
- ERP supplier master
- ERP financial master
- ERP inventory balances
- ERP transactional records

where the customer has explicitly designated those systems as the system of record.

Phoenix modules may own domains where Phoenix is explicitly designated as the system of record.

Integration architecture must define:

- System of record
- Data ownership
- Synchronization direction
- Synchronization frequency or trigger
- Conflict resolution
- Identifier mapping
- Failure handling
- Audit requirements
- Tenant/security context
- Read-model/projection requirements

Phoenix must not create duplicate authoritative masters simply because an external system is connected.

This rule applies to future ERP, WMS, accounting, CRM, manufacturing and other external-system integrations.

## 27. Phase 3.3 Implementation Status

Phase 3.3 has been implemented and validated against the complete Phoenix Core V2 regression suite.

Implementation includes:

- Module integration contracts
- Module dependency contracts
- Capability discovery
- Synchronous module invocation
- Command contracts
- Query contracts
- Event contracts
- Event subscriptions
- Event bus infrastructure
- Durable event delivery
- Integration context propagation
- Authorization and entitlement enforcement
- Dependency/version compatibility
- Circular dependency detection
- Retry handling
- Idempotent event delivery
- Core Job infrastructure integration
- Module lifecycle integration
- Integration architecture hardening
- Core/Framework dependency boundary enforcement

Validation result:

**Full Phoenix Core V2 regression: 578 tests passed.**

No regression failures were present at the Phase 3.3 completion gate.

Phase 3.3 is therefore considered **implemented, tested and ready for architectural freeze**, subject to the final Git commit and repository push.

## 28. Architectural Status

ADR-039 remains **Accepted**.

Phase 3.3 implementation confirms the architectural decision in executable code and automated tests.

The architecture is now the authoritative contract for Phoenix V2 module integration.

Future changes to module integration must extend or explicitly supersede this ADR rather than introducing parallel integration patterns.

