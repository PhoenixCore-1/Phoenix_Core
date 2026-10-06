# SPEC-001 - Production 360

## Background

Phoenix Production 360 is the manufacturing business module implemented within the Phoenix Core platform.

Phoenix Core remains authoritative for authentication, identity, organisations/companies, memberships, permissions, entitlements, sessions, platform context, and module lifecycle.

Production 360 is a business module inside the existing Core User Platform, not a fourth platform.

Production owns the manufacturing domain and its business rules, including manufacturing orders, production stages and lifecycle, production quantities, reconciliation, BOM/SPC context, ETA calculation, production risk, holds, and operational production reporting.

The intended user journey is:

Login -> Phoenix Core User Platform -> Production 360 -> Production Operations Workspace

Core remains the system of record for platform concerns while Production remains the system of record for manufacturing-domain concerns.

The Production 360 implementation has progressed through WP1-WP8 covering the Production domain foundation, persistence and services, operational API, User Platform integration, frontend workspace, and development-environment Core activation.

This specification establishes the authoritative Production 360 architecture, requirements, implementation boundary, milestones, and MVP handover position.

## Requirements

### Must Have

- Production 360 MUST operate as a business module within the Phoenix Core User Platform.
- Phoenix Core MUST remain authoritative for authentication, identity, organisation/company context, memberships, permissions, entitlements, sessions, platform context, and module lifecycle.
- Production MUST NOT introduce an independent authentication, organisation, permission, entitlement, or session system.
- Production data MUST be isolated by organisation_id.
- Production HTTP APIs MUST enforce Core request context, entitlement, permission, and organisation boundaries.
- The system MUST support the Production manufacturing-order lifecycle and production-stage execution.
- Production MUST record planned and actual production quantities.
- Quantity history MUST remain auditable and support reconciliation.
- BOM and SPC context MUST remain controlled and historically traceable.
- Production MUST provide ETA information and support configurable working days, weekends, and public holidays.
- Production MUST expose schedule risk and required-date risk.
- Production MUST support production-order holds and resumption.
- The Core User Platform MUST provide access to Production 360 when the required module entitlement and permission are present.
- Production 360 MUST provide operational views for performance, orders, ETA/risk, and active holds.
- Server-side Core authorization MUST remain the security boundary.

### Should Have

- Order count, open order count, completed order count, planned quantity, actual quantity, completion ratio, production time, and production rate.
- Operational attention indicators for ETA action required, schedule risk, required-date risk, and active holds.
- Consistent Production module navigation.
- Request correlation through the Core request context.
- A consolidated operational snapshot API.

### Could Have

- Additional Production analytics and visualisations.
- Advanced production planning.
- Additional cross-module Production integrations.
- Additional Production workflow capabilities.
- Future AI-assisted Production capabilities operating within Core AI governance.

### Won't Have in this MVP

- Separate Production authentication.
- Separate Production users.
- Separate Production organisations.
- Separate Production permissions.
- Separate Production entitlements.
- Separate Production sessions.
- UI-only security enforcement.
- A database ownership model that bypasses Core.
- AI-generated production decisions that override authoritative Production rules.

## Method

### Architecture

Production 360 follows:

    Phoenix Core
    |-- System Platform
    |-- Company Platform
    -- User Platform
          -- Production 360

Production 360 is therefore a business module inside the User Platform.

### Responsibility Model

| Responsibility | Owner |
|---|---|
| Authentication | Phoenix Core |
| Identity | Phoenix Core |
| Organisation | Phoenix Core |
| Company context | Phoenix Core |
| Membership | Phoenix Core |
| Roles | Phoenix Core |
| Permissions | Phoenix Core |
| Entitlements | Phoenix Core |
| Sessions | Phoenix Core |
| Module lifecycle | Phoenix Core |
| Request context | Phoenix Core |
| Production orders | Production |
| Production stages | Production |
| Production quantities | Production |
| Reconciliation | Production |
| BOM | Production |
| SPC | Production |
| ETA | Production |
| Production risk | Production |
| Holds | Production |
| Production operational UI | Production 360 |

### Core Request Context

Production uses the existing Core request context:

    RequestContext
    |-- request_id
    |-- identity_id
    |-- organisation_id
    |-- session_id
    |-- permissions
    -- entitlements

### Authorisation Flow

    User
     |
     v
    Core Authentication
     |
     v
    Core Platform Context
     |
     v
    User Platform
     |
     v
    Production 360
     |
     v
    Production API
     |-- production entitlement
     -- production.view permission
     |
     v
    Production Service
     |
     v
    Production Domain

Frontend visibility is not the security boundary. The Production API independently enforces entitlement and permission.

### Module Contract

Production module entitlement: production

Primary MVP read permission: production.view

Production permissions:

    production.view
    production.order.create
    production.order.edit
    production.order.release
    production.order.execute
    production.quantity.record
    production.quantity.adjust
    production.bom.view
    production.bom.manage
    production.spc.view
    production.spc.manage
    production.eta.view
    production.eta.recalculate
    production.ai.use
    production.admin

Production capabilities:

    production.orders
    production.execution
    production.quantity
    production.bom
    production.spc
    production.eta

Integration contracts:

    production.order.lifecycle
    production.quantity.recording
    production.eta.snapshot

Integration events:

    production.order.released
    production.order.started
    production.order.stage_started
    production.order.held
    production.order.resumed
    production.order.completed
    production.quantity.recorded

### Operational API

Primary MVP endpoint:

    GET /api/v1/production/operational-snapshot

Performance endpoint:

    GET /api/v1/production/performance

The operational snapshot contains organisation_id, performance, orders, and order_count.

Performance contains order_count, open_order_count, completed_order_count, planned_quantity, actual_quantity, completion_ratio, total_production_seconds, average_production_seconds, and average_actual_rate.

Operational orders contain production_order_id, status, planned_quantity, required_date, eta, and active_hold_count.

ETA information contains planned_eta, current_eta, required_date, schedule_risk, required_date_risk, decision, action_required, and summary.

### Operational Attention

An order requires operational attention when one or more of these conditions exist:

    ETA action_required
    OR schedule risk
    OR required-date risk
    OR active holds

### Golden Path

    Product
     |
     v
    BOM + SPC
     |
     v
    Manufacturing Order
     |
     v
    Release
     |
     v
    Material Requirements + SPC Snapshot
     |
     v
    Start
     |
     v
    Stage Execution
     |
     v
    Quantity Recording
     |
     v
    Reconciliation
     |
     v
    ETA / Risk
     |
     v
    Complete
     |
     v
    Audit + History

### PlantUML Architecture

`plantuml
@startuml
package "Phoenix Core {
  [Authentication]
  [Platform Context]
  [Module Service]
  [Entitlement Service]
  [Authorization Service]
  [Role Service]
  database "Core DB as DB
}

package "Production 360 {
  [Production HTTP API] as API
  [Production Service] as Service
  [Production Domain] as Domain
  [Production User Interface] as UI
}

[Authentication] --> [Platform Context]
[Platform Context] --> API
[Module Service] --> DB
[Entitlement Service] --> DB
[Authorization Service] --> DB
[Role Service] --> DB
UI --> API
API --> [Entitlement Service]
API --> [Authorization Service]
API --> Service
Service --> Domain
Domain --> DB
@enduml
`"
"


### WP1 - Production Domain Foundation

**Status: COMPLETE**

Established the Production domain foundation and Core module integration contract.

### WP2 - Persistence and Core Domain Services

**Status: COMPLETE**

Implemented the Production persistence and service foundation within the established Core architecture.

### WP3 - Production Lifecycle and Operational Domain

**Status: COMPLETE**

Implemented Production lifecycle and operational domain behaviour.

### WP4 - Production Audit and Existing Implementation Validation

**Status: COMPLETE**

Audited and mapped the existing Production implementation against the Phoenix Core architecture.

### WP5 - Production Domain Completion

**Status: COMPLETE**

Completed the Production domain functionality required for the agreed Production 360 baseline.

### WP6 - Production Operationalisation / API

**Status: COMPLETE**

Implemented the Production operational HTTP/API boundary.

Final full-suite result: 1026 passed, 19 warnings.

Commit: 8b8fec1 - feat: complete Production 360 WP6 API operationalization

### WP7 - Production 360 User Platform Integration

**Status: COMPLETE**

Implemented the Core User Platform and Production workspace integration.

Routes:

    /user
    /user/production
    /user/production/performance
    /user/production/orders
    /user/production/eta-risk
    /user/production/holds

### WP8 - Production Core Activation

**Status: COMPLETE FOR DEVELOPMENT MVP**

Development database: .local/phoenix_core_v1_dev.db

Development activation:

    Production module       ENABLED
    Production version     1.3.25
    DEMO organisation      ACTIVE
    production entitlement ACTIVE
    DEMO.PRODUCTION.USER   ACTIVE
    production.view        ASSIGNED
    demo.user              ASSIGNED

### Existing Code

src/production/Production360.tsx is effectively superseded by src/production/ProductionShell.tsx and remains intentionally retained unless separately removed as cleanup work.

## Milestones

| Milestone | Status |
|---|---|
| WP1 - Production domain foundation | COMPLETE |
| WP2 - Persistence and Core services | COMPLETE |
| WP3 - Lifecycle and operational domain | COMPLETE |
| WP4 - Audit and mapping | COMPLETE |
| WP5 - Production domain completion | COMPLETE |
| WP6 - Operational API | COMPLETE |
| WP7 - User Platform integration | COMPLETE |
| WP8 - Development Core activation | COMPLETE |
| Core baseline context verification | NEXT |
| Browser E2E smoke test | NEXT |
| Final MVP handover verification | PENDING |
| Release note | AFTER FINAL VERIFICATION |
| Final release commit/tag | AFTER FINAL VERIFICATION |

## Gathering Results

### Current Results

Production 360 has completed the agreed WP1-WP8 implementation sequence.

The resulting architecture is:

    Core Authentication
     |
     v
    Core User Platform
     |
     v
    Production Entitlement
     |
     v
    Production Permission
     |
     v
    Production 360
     |
     v
    Production Operational API
     |
     v
    Production Domain
     |
     v
    Core Database

### Test Results

WP6 full-suite result: 1026 passed, 19 warnings.

Frontend build validation was completed during WP7.

### Development Activation

The development environment has the Production module enabled and the required organisation entitlement and production.view permission assigned to the demonstration user.

### Remaining Verification

1. Core baseline context verification: verify GET /api/v1/baseline/context and confirm the activated user receives the expected user, company, module, permission, and entitlement context.

2. Browser E2E smoke test: verify Login -> User Platform -> Production 360 -> Overview -> Performance -> Orders -> ETA & Risk -> Holds -> Back to User Platform.

Direct-route access and server-side security enforcement must also be verified.

### Release Position

Production 360 is complete through WP8.

The release note and final release commit/tag should be created only after the Core baseline-context and browser E2E verification steps pass.

## Handover Position

The current Phoenix Core development architecture is represented by:

    Phoenix Core
    |-- System Platform
    |-- Company Platform
    |-- User Platform
          -- Production 360
                |-- Production API
                |-- Production Domain
                |-- Production Operations
                |-- ETA / Risk
                -- Holds

Core remains the platform system of record.

Production remains the manufacturing-domain system of record.

The next sequence is:

    Core baseline context verification
     |
     v
    Browser E2E smoke test
     |
     v
    Final MVP verification
     |
     v
    Release note
     |
     v
    Final release commit/tag

## Change History

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-26 | Initial consolidated Production 360 specification established from the WP1-WP8 implementation baseline. |

## Need Professional Help in Developing Your Architecture?

Please contact me at https://sammuti.com
