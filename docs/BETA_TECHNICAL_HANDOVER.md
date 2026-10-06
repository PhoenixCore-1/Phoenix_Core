# SPEC-001 — Phoenix Core Beta Technical Handover

**Document version:** v0.2
**Product:** Phoenix Core
**Target release:** v1.0.0
**Current development version:** v1.0.0-alpha.1
**Current phase:** Alpha / preparation for Beta
**Primary branch:** `main`
**Current Git baseline:** `192af5a`
**Customer Master checkpoint:** `85600c6`
**Document status:** Live development control document

---

## Background

Phoenix Core is being developed toward its first official production release, **v1.0.0**.

The project has reached a point where development needs to proceed through clearly separated technical workstreams rather than through a single-person development flow.

The purpose of this document is to provide a **live technical handover and development control point** for the Phoenix Core development team.

This document exists to ensure that:

- Darian can take technical development forward without needing to reconstruct the project's history from individual conversations.
- Jaco remains closely involved in product vision, requirements, architectural direction and prioritisation.
- Development work can proceed in parallel without duplicated or conflicting work.
- Git remains the authoritative source for application code.
- This document remains the authoritative source for the **current development state, technical boundaries, dependencies and next actions**.
- Daily development status is recorded separately so that the project retains an auditable history of decisions, checkpoints, tests and unfinished work.

The handover is intended to evolve with the project.

The current operating model has now been expanded to explicitly support parallel development between Company Platform and Production 360 while requiring coordinated decisions at shared architectural boundaries.

It is not a replacement for the source code, product requirements or detailed architecture documentation. It is the **current technical control document** that connects those artefacts to active development.

### Current Baseline

The current `main` branch has been verified clean and synchronised with GitHub at:

`192af5a` — `docs: add Beta technical handover`

The current Phoenix Core development version is:

`v1.0.0-alpha.1`

The first official production release is intended to be:

`v1.0.0`

The Customer Master import workflow is the current verified functional development baseline.

---

## Requirements

The Beta development phase must establish a controlled, testable and deployable foundation for Phoenix Core's first official release, `v1.0.0`.

Requirements are prioritised using MoSCoW.

### Must Have

- **M1 — Stable development baseline:** All development must start from a known, clean Git checkpoint.
- **M2 — Functional core workflows:** Approved Phoenix Core Beta functionality must be implemented end-to-end, including backend, API, database and frontend components where applicable.
- **M3 — Data integrity:** Business-critical data operations must use explicit validation, appropriate transaction boundaries and safe failure/rollback behaviour.
- **M4 — Authorisation:** Existing permission boundaries must be respected. New permissions may be introduced where required by an approved feature, but Beta is not a general RBAC redesign.
- **M5 — Test coverage:** New or materially changed functionality must have appropriate automated tests.
- **M6 — Development traceability:** Meaningful development sessions must end with a Git checkpoint and an update to the technical handover.
- **M7 — Parallel development:** Workstreams must have defined ownership, boundaries and dependencies so that Jaco and Darian can work in parallel without conflicting changes.
- **M8 — Release versioning:** Phoenix Core must progress through:
  `v1.0.0-alpha.N` → `v1.0.0-beta.N` → `v1.0.0-rc.N` → `v1.0.0`

### Should Have

- **S1 — Clear technical ownership:** Darian leads implementation and technical development while Jaco remains responsible for product direction, requirements, architectural direction and prioritisation.
- **S2 — Documented architecture:** Important architectural decisions, interfaces, database structures and system boundaries must be documented sufficiently for another developer to implement or maintain them.
- **S3 — Daily handover:** A daily status document should record completed work, Git checkpoint, tests, unfinished work, issues/decisions and next actions.
- **S4 — Known-issue tracking:** Pre-existing failures and technical debt must be explicitly distinguished from regressions introduced by new work.
- **S5 — Controlled scope:** Completed functionality should not be casually refactored during Beta unless the change is necessary for an approved requirement, defect or architectural decision.

### Could Have

- **C1 — Additional developer tooling:** CI/CD automation, expanded quality gates and development automation where they provide clear value without delaying Beta.
- **C2 — Additional technical documentation:** Deeper component-level documentation where implementation complexity warrants it.
- **C3 — Additional automated regression coverage:** Expansion beyond the coverage required for critical Beta workflows.

### Won't Have During Beta Unless Explicitly Approved

- **W1 — General RBAC redesign**
- **W2 — Repository restructuring**
- **W3 — Unrelated platform refactoring**
- **W4 — Unrelated Production 360 refactoring**
- **W5 — Broad technology changes without a demonstrated Beta requirement**
- **W6 — Scope expansion merely because an improvement is technically desirable**

### Requirement Change Rule

Any requirement that materially changes an agreed Beta workflow, database contract, API contract, architecture boundary or workstream dependency must be recorded in this document before implementation proceeds.

---

## Method

Phoenix Core Beta development will use a controlled modular architecture with clearly separated workstreams.

The objective is to allow parallel implementation while protecting shared contracts, database integrity, security boundaries, completed functionality, product scope and release stability.

### 3.1 System Development Model

The current development model is:

```text
                    ┌─────────────────────┐
                    │    Phoenix Core     │
                    │      v1.0.0         │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      System Platform   Company Platform   User Platform
             │                 │                 │
             │                 ▼                 │
             │          Business Modules        │
             │                 │                 │
             │                 ▼                 │
             │          Production 360          │
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                       Shared Foundation
                 ┌─────────────┼─────────────┐
                 │             │             │
                 ▼             ▼             ▼
              Database       HTTP/API      Security
```

The architecture is intentionally modular at the application and domain boundaries while avoiding unnecessary framework or repository restructuring during Beta.

### 3.2 Development Workstreams

Development will be divided into independently trackable workstreams.

| Workstream | Purpose | Primary Responsibility | Dependency |
|---|---|---|---|
| Product & Requirements | Product vision, requirements and prioritisation | Jaco | Business direction |
| Architecture | Solution architecture and cross-module decisions | Jaco + Darian | Product requirements |
| Technical Development | Implementation, code quality and technical delivery | Darian | Approved requirements/architecture |
| Company Platform | Company-level business functionality | Assigned per task | System Platform |
| System Platform | Shared platform capabilities | Assigned per task | Core foundation |
| User Platform | User-facing platform capabilities | Assigned per task | System Platform |
| Production 360 | Production-related business functionality | Protected reference area | Existing architecture |
| QA & Verification | Automated and manual verification | Development team | Completed implementation |
| Documentation & Handover | Current state, decisions and daily status | Development team | All workstreams |

Specific feature ownership may change. The table defines responsibilities and boundaries rather than permanently assigning every module to one person.

### 3.3 Ownership Model

#### Jaco

Jaco remains actively involved in:

- Product vision
- Business requirements
- Feature prioritisation
- Acceptance criteria
- High-level architectural direction
- Approval of material scope changes
- Approval of material architectural changes
- Product-level trade-offs

#### Darian

Darian leads:

- Technical implementation
- Code-level architecture
- Engineering practices
- Technical task breakdown
- Automated testing
- Technical investigation
- Development coordination
- Technical readiness for release
- Technical implementation decisions within the agreed architecture

#### Shared Decisions

Material architectural decisions are collaborative where they affect product direction, system boundaries, shared contracts, database architecture, security architecture, significant future development or release risk.

The objective is not to remove Jaco from technical development. The objective is to allow Darian to lead implementation while Jaco continues to shape the product and architecture.

### 3.4 Change Boundaries

A developer may freely modify files within an assigned workstream when the change does not alter a shared contract.

The following are considered shared-change areas:

- Database migrations affecting multiple modules
- Shared database tables
- Public or internal API contracts
- Authentication foundations
- Authorisation foundations
- Shared frontend components
- Shared configuration
- Core domain interfaces
- Cross-module events
- Integration contracts
- Repository-wide build configuration
- Deployment configuration

Changes to shared areas require coordination before implementation.

### 3.5 Git Control

Git is the authoritative source of application code.

The development sequence is:

```text
Requirement
    │
    ▼
Technical assessment
    │
    ▼
Workstream assignment
    │
    ▼
Feature branch
    │
    ▼
Implementation
    │
    ▼
Automated tests
    │
    ▼
Git checkpoint
    │
    ▼
Pull Request
    │
    ▼
Review / Verification
    │
    ▼
main
```

No meaningful development work should be performed directly on `main`.

Every meaningful development session must leave a recoverable Git checkpoint.

### 3.6 Technical Handover Control

`docs/BETA_TECHNICAL_HANDOVER.md` is the authoritative source for the **current development state**.

It must identify:

- Current Git baseline
- Current release/version
- Completed functionality
- Active workstreams
- Work in progress
- Dependencies
- Known problems
- Architectural decisions
- Safe next actions
- Work that must not currently be modified

Historical daily records are stored under:

```text
docs/status/YYYY-MM-DD.md
```

The main handover describes the current state. Daily status documents describe what happened during individual development sessions.

### 3.7 Development Safety Rules

1. Do not modify another developer's active workstream without coordination.
2. Do not silently change shared interfaces.
3. Do not rewrite completed functionality merely for preference during Beta.
4. Do not combine unrelated refactoring with feature implementation.
5. Do not treat a pre-existing test failure as a regression without verification.
6. Every database change requires an explicit migration.
7. Every API contract change must be documented.
8. Every meaningful feature must have appropriate automated verification.
9. Scope changes must be agreed before implementation.
10. When uncertain about ownership or dependency, stop and clarify rather than modifying shared code.

### 3.8 Current Verified Customer Master Baseline

The Customer Master import workflow is the first explicitly documented technical baseline for the handover.

Current implementation checkpoint:

`85600c6` — `feat: complete customer master import workflow`

Scope:

```text
System Platform
    ↓
Company Platform
    ↓
Imports / Exports
    ↓
Customer Master
```

The approved workflow is:

```text
Company Admin
      │
      ▼
Upload Customer Master
      │
      ▼
Create Import Job
      │
      ▼
Validate
      │
      ▼
Preview
      │
      ▼
Explicit Admin Confirmation
      │
      ▼
Atomic Commit
      │
      ▼
Customer Reference Data
```

### Explicitly Out of Scope

The Customer Master implementation does not include:

- Product / Item Master
- Warehouse Master
- Inventory refactoring
- Production refactoring
- System Platform refactoring
- RBAC redesign
- Module/plugin architecture redesign
- Repository restructuring
- Production 360 refactoring

Production 360 remains a working reference and must not be refactored as part of the Customer Master work.

### 3.9 Customer Master Backend

Primary implementation:

```text
src/phoenix_company/application/customer_import_parser.py
src/phoenix_company/application/customer_imports.py
```

The application service exposes:

```text
create_import_job()
validate_import_job()
get_import_preview()
confirm_import()
```

The HTTP layer remains thin and delegates workflow and authorisation decisions to the application service.

### 3.10 Customer Master Parser

Supported file formats:

```text
.xlsx
.xlsm
.csv
```

Excel processing uses:

```text
openpyxl >= 3.1.5, < 4
```

The parser:

- Uses the `Customers` worksheet when present.
- Otherwise uses the first worksheet.
- Reads the workbook as a matrix.
- Handles the 203-column Customer Master structure.
- Locates Customer ID and Customer Name columns.
- Detects missing required columns.
- Detects missing customer IDs.
- Detects duplicate customer IDs.
- Detects missing customer names.
- Performs row-level validation.
- Produces a preview of the first 25 rows.

The verified Customer Master workbook contained:

```text
10,706 records
203 columns
10,706 valid
0 invalid
25 preview rows
```

### 3.11 Customer Master Database

Migration:

```text
migrations/036_company_customer_imports.sql
```

The import system uses three primary tables:

```text
import_jobs
import_job_rows
customer_references
```

#### `import_jobs`

Primary fields:

```text
id
organisation_id
import_type
source_filename
source_system
status
uploaded_by
uploaded_at
validated_at
confirmed_at
completed_at
total_rows
valid_rows
invalid_rows
warning_rows
inserted_rows
updated_rows
unchanged_rows
file_hash
error_summary
created_at
updated_at
```

#### `import_job_rows`

Primary fields:

```text
id
import_job_id
row_number
external_id
warehouse_external_id
raw_data_json
validation_status
validation_errors_json
validation_warnings_json
action
```

#### `customer_references`

Primary fields:

```text
id
organisation_id
source_system
external_customer_id
display_name
status
source_record_url
created_at
updated_at
```

Customer identity is:

```text
organisation_id
+
source_system
+
external_customer_id
```

The V1 scope uses:

```text
source_system = PHOENIX
```

There is no source-system selection UI/API in the current scope.

### 3.12 Customer Master Import Decision Algorithm

For each valid imported record:

```text
                 ┌──────────────────┐
                 │ External ID      │
                 │ exists?          │
                 └────────┬─────────┘
                          │
                 ┌────────┴────────┐
                 │                 │
                NO                YES
                 │                 │
                 ▼                 ▼
              INSERT       Data identical?
                                 │
                         ┌───────┴───────┐
                         │               │
                        YES              NO
                         │               │
                         ▼               ▼
                     UNCHANGED         UPDATE
```

Invalid records are rejected. They must not be committed as valid customer reference data.

### 3.13 Customer Master Transaction Behaviour

Confirmation uses an atomic database transaction.

The transaction:

1. Begins an immediate transaction.
2. Validates that the import job is in the expected state.
3. Processes validated rows.
4. Applies INSERT / UPDATE / UNCHANGED decisions.
5. Updates import counters.
6. Marks the job `COMPLETED`.
7. Commits.

If an error occurs during processing:

```text
Transaction
    ↓
Failure
    ↓
Rollback
    ↓
No partial confirmation
```

The objective is all-or-nothing confirmation.

### 3.14 Customer Master API

Current API endpoints:

```text
POST /api/v1/company/imports/customer-master
GET  /api/v1/company/imports/{job_id}/preview
POST /api/v1/company/imports/{job_id}/confirm
```

The frontend uses:

```text
frontend/phoenix-platform/src/company/imports/customerMaster/api.ts
```

File uploads use `FormData`.

The shared API client handles the upload request.

API contracts must not be changed casually during Beta.

Any material API contract change must identify:

- Reason
- Existing consumers
- Migration impact
- Test impact
- Backward compatibility requirements

### 3.15 Customer Master Authorisation

Customer Master import functionality uses:

```text
company.data.import
```

Expected role:

```text
COMPANY.ADMIN
```

Beta development is not a general RBAC redesign.

Existing RBAC structures should be extended only where an approved feature requires it.

An existing UUID RoleService test issue was handled by directly inserting the required role-permission relation in the test rather than modifying production RBAC architecture.

### 3.16 Customer Master Tests

Customer Import application tests:

```text
5 passed
```

Coverage includes:

- Insert
- Unchanged
- Update
- Invalid rejection
- Transaction rollback

HTTP tests:

```text
7 passed
```

Full backend baseline:

```text
1036 passed
4 failed
20 warnings
```

The four failures were identified as pre-existing baseline issues:

1. Secure session cookie expected `Secure`, while current behaviour is `HttpOnly; Path=/; SameSite=lax`.
2. Existing company-admin creation test expects HTTP 200 but current foundation returns HTTP 422.
3. Company permission count expects 8 while the current foundation has 9 because `company.data.import` is required.
4. Local database architecture test detects a root-level `phoenix.db`.

These failures must not automatically be treated as Customer Master regressions.

Warnings included:

- FastAPI / Starlette TestClient
- httpx
- anyio
- Python 3.12 SQLite datetime adapter

These warnings were considered non-blocking for the Customer Master checkpoint.

### 3.17 Customer Master Protected Files

The verified Customer Master checkpoint contains the following key files:

```text
frontend/phoenix-platform/src/company/imports/customerMaster/api.ts
pyproject.toml
src/phoenix_company/application/customer_import_parser.py
src/phoenix_company/application/customer_imports.py
src/phoenix_core/http_api/company.py
tests/company/test_customer_imports_application.py
tests/http_api/test_customer_imports.py
```

The Customer Master implementation should be treated as a protected completed baseline unless:

- a defect is discovered,
- a Beta requirement requires a change,
- an API/database contract must legitimately evolve,
- or an explicit architectural decision authorises the change.

### 3.18 Baseline Failure Rule

The distinction between baseline failures and new regressions is mandatory.

```text
Existing baseline failure
        �
Regression introduced by new work
```

When a new feature is developed:

1. Run the relevant existing tests.
2. Record baseline failures.
3. Implement the feature.
4. Run the same tests again.
5. Determine whether the failure existed before the change.
6. Record any new failure as a regression.
7. Do not silently modify unrelated code to make tests green.

A baseline issue should become a separate task unless resolving it is directly required by the active Beta scope.

### 3.19 Safe Parallel Development Model

The team will use parallel workstreams where dependencies permit.

```text
                         Approved Requirement
                                │
                                ▼
                       Architecture / Contract
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
           Backend API      Database        Frontend
                │               │               │
                └───────────────┼───────────────┘
                                ▼
                           Integration
                                │
                                ▼
                              Tests
                                │
                                ▼
                              main
```

Parallel development is permitted when:

- The interface is understood.
- Dependencies are known.
- Workstreams do not modify the same active implementation unnecessarily.
- Shared contracts are coordinated first.

Parallel development is not permission to independently modify shared foundations.

### 3.20 Safe-Next-Work Decision Model

Before starting work, the developer should answer:

1. What requirement am I implementing?
2. Which workstream owns it?
3. What files/modules will I modify?
4. What shared contracts are involved?
5. What dependencies must already exist?
6. What tests prove the change works?
7. What existing functionality must remain untouched?

If these questions cannot be answered confidently, the developer should stop and clarify the dependency or ownership before changing shared code.

### 3.21 Agreed Beta Parallel Development Model

The agreed Beta operating model is:

> **Parallel implementation, coordinated architectural decisions.**

Jaco and Darian may work on separate active workstreams at the same time, but workstream ownership does not grant unilateral authority over shared architecture.

The intended split is:

| Area | Primary lead | Operating rule |
|---|---|---|
| Product vision, requirements and prioritisation | Jaco | Jaco remains deeply involved |
| Production 360 | Jaco | Continue development independently where Core dependencies permit |
| Company Platform implementation | Darian | Darian leads implementation of agreed Company Platform work |
| Shared architecture | Jaco + Darian | Material decisions are discussed and agreed before implementation |
| Cross-module contracts | Jaco + Darian | Agree the contract before either side builds against it |
| Git / technical handover | Shared | Every meaningful development session leaves a checkpoint and current status |

The purpose is to give Darian enough ownership to move quickly without creating a second, incompatible architectural direction for Phoenix.

### 3.22 Company Platform → Production 360 Boundary

For Beta, the architectural ownership boundary is:

> **Company Platform owns authoritative company/master/reference data. Production 360 owns production-specific operational behaviour.**

Company Platform owns the authoritative definitions and lifecycle of data such as:

- Customers
- Products / Items
- Warehouses / Locations
- Other company-level reference data
- Company documents and approved metadata
- Core-level integrations and shared capabilities

Production 360 owns:

- Production orders/jobs
- Production planning
- Production scheduling
- Production execution
- Production status/lifecycle
- Production-specific calculations
- Production-specific workflows and reporting

Production 360 consumes authoritative Company Platform data through agreed Core interfaces. It must not create competing authoritative master-data systems.

Where a production record needs a Company Platform entity, the preferred identity model is to reference the stable Phoenix internal ID (for example `customer_id`, `product_id`, `warehouse_id`). External/import identifiers remain part of the Core master-data identity model and should not become competing Production identities.

### 3.23 Beta-to-Production Architecture Principle

The current Beta architecture contains Production 360 within the existing Phoenix Core application architecture. This is accepted for Beta.

Beta is **not** the phase for a broad Production 360 extraction/refactoring exercise.

The target architecture for the final production release is:

```text
                         PHOENIX CORE
                 ┌─────────────────────────┐
                 │ Identity / Organisation  │
                 │ Company Master Data      │
                 │ Shared Services          │
                 │ Permissions / Security   │
                 │ Core APIs / Contracts    │
                 └────────────┬────────────┘
                              │
                       Controlled Gates
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │ Production   │    │ Future       │    │ Future       │
   │ 360 Module   │    │ Module       │    │ Module       │
   │ Standalone   │    │ Standalone   │    │ Standalone   │
   └──────────────┘    └──────────────┘    └──────────────┘
```

The final release should enforce module boundaries through controlled interfaces/gates to Core.

Therefore:

- Do not break Production 360 out during Beta unless explicitly required.
- Do not duplicate Core master data inside Production 360.
- Build Beta interfaces with the future modular boundary in mind.
- Treat modularisation as a deliberate post-Beta/release-readiness architecture phase.

### 3.24 Darian Company Platform Beta MVP

Darian's Company Platform Beta objective is:

> **Build the minimum Company Platform capabilities required to make Phoenix Core + Production 360 a viable Beta product.**

The approved capability areas are:

1. **Production 360 data enablement**
   - Customer Master
   - Product / Item Master
   - Warehouse / Location Master
   - Additional reference data explicitly required by Production 360
2. **Sage integration**
   - Required Sage API/data exchange for Beta
3. **Company Documents**
   - MSDS
   - Data sheets
   - Other approved company/product documents
4. **Phoenix Connect**
   - Agreed Beta connectivity/integration capability
5. **Phoenix AI**
   - Agreed initial AI MVP use cases

This is an MVP boundary. It is not permission to expand into a generic integration platform, document platform, AI platform or broad Core refactor during Beta.

### 3.25 Beta Backlog and Dependency Sequence

The working priority sequence is:

```text
Production 360 data enablement
            ↓
        Sage API
            ↓
       Documents
            ↓
     Phoenix Connect
            ↓
       Phoenix AI
```

This is a dependency preference, not a requirement that every item finish before the next can start. Independent work may proceed in parallel.

#### Workstream A — Production 360 Data Enablement

| Priority | Capability | Lead | Completion condition |
|---|---|---|---|
| MUST | Customer Master | Darian | Existing workflow remains verified and protected |
| MUST | Product / Item Master | Darian | Required Production product data can be imported/exported and consumed through agreed Core interfaces |
| MUST | Warehouse / Location Master | Darian | Required Production warehouse/location data is available through agreed Core interfaces |
| MUST | Additional Production reference data | Darian | Every required data domain has an agreed source, schema and interface |
| MUST | Production ↔ Core contracts | Jaco + Darian | IDs, ownership, required fields and interface behaviour are agreed |

#### Workstream B — Sage Integration

| Priority | Capability | Lead | Completion condition |
|---|---|---|---|
| MUST | Sage API connectivity | Darian | Phoenix can securely communicate with the required Sage environment |
| MUST | Required Beta data exchange | Darian | Only agreed Beta Sage data is exchanged reliably |
| MUST | Error/status handling | Darian | Integration failures are visible and recoverable |
| MUST | Production dependency mapping | Jaco + Darian | Production workflows identify when Sage data is required |

#### Workstream C — Company Documents

| Priority | Capability | Lead | Completion condition |
|---|---|---|---|
| MUST | Document upload | Darian | Authorised Company users can upload approved document types |
| MUST | MSDS support | Darian | MSDS documents can be stored/retrieved against the correct Core entity |
| MUST | Data sheet support | Darian | Data sheets can be stored/retrieved |
| MUST | Document metadata | Darian | Required identity, type, entity association, filename, version/status and audit information are maintained |
| MUST | Access control | Jaco + Darian | Documents are available only through authorised Core access |
| SHOULD | Production document consumption | Jaco + Darian | Production 360 can retrieve documents it legitimately requires |

#### Workstream D — Phoenix Connect

| Priority | Capability | Lead | Completion condition |
|---|---|---|---|
| MUST | Beta Connect foundation | Darian | Agreed Beta connectivity capability works end-to-end |
| MUST | Core integration | Darian | Connect uses approved Core interfaces |
| MUST | Error/status visibility | Darian | Failed or incomplete connections are identifiable |
| SHOULD | Production integration | Jaco + Darian | Production 360 can use Connect where required |

Phoenix Connect must remain a Beta capability rather than becoming a generic integration-platform project.

#### Workstream E — Phoenix AI

| Priority | Capability | Lead | Completion condition |
|---|---|---|---|
| SHOULD | Agreed AI MVP use case | Darian | Previously agreed Beta AI use case works end-to-end |
| SHOULD | Authorised Core data/document access | Darian | AI accesses only approved information |
| SHOULD | Output/error handling | Darian | AI responses and failures are handled safely and visibly |
| COULD | Additional AI capabilities | Later | Considered only after MUST/SHOULD Beta scope is stable |

AI scope must remain tightly bounded during Beta.

### 3.26 One-Capability-at-a-Time Darian Onboarding Model

Darian should not be handed the entire Company Platform Beta backlog as one implementation task.

The operating model is:

```text
Select next capability
        ↓
Review existing implementation
        ↓
Confirm requirement / contract
        ↓
Implement one bounded capability
        ↓
Test
        ↓
Git checkpoint
        ↓
Update technical handover
        ↓
Select next capability
```

The first task should be deliberately small and concrete.

Darian's first assignment is:

> **Take the next Production 360-required Company Platform data capability after Customer Master and complete it end-to-end, using Customer Master as the reference implementation.**

The exact capability should be selected from the actual Production 360 dependency list rather than being chosen speculatively.

Jaco remains available to provide Phoenix/Production context and to make or jointly make architectural decisions. Jaco should assist when that context materially accelerates Darian rather than taking over implementation by default.

### 3.27 Joint Decision Gates

Darian should stop and discuss the change with Jaco before implementation when it affects:

- Shared database structures
- Core ↔ Production API contracts
- Identity/ID strategy
- Authentication or authorisation boundaries
- Shared services
- Cross-module ownership
- Major architectural patterns
- Significant future modularisation implications
- Material Beta scope or release risk

Once the contract/decision is agreed, Darian can implement within the agreed boundary without waiting for the entire surrounding workstream to be complete.

---

## Implementation

Implementation will proceed through controlled workstreams rather than a single sequential development queue.

### 4.1 Development Cycle

Each feature follows this cycle:

```text
1. Requirement
      ↓
2. Acceptance criteria
      ↓
3. Architecture / dependency assessment
      ↓
4. Workstream assignment
      ↓
5. Feature branch
      ↓
6. Implementation
      ↓
7. Automated tests
      ↓
8. Manual verification where required
      ↓
9. Git checkpoint
      ↓
10. Pull Request
      ↓
11. Review
      ↓
12. Merge
      ↓
13. Handover update
```

### 4.2 Branching

Branches should describe the purpose of the work.

Examples:

```text
feature/customer-master-ui
feature/product-master
feature/warehouse-master
fix/customer-import-validation
chore/ci-quality-gates
docs/beta-handover
```

Avoid ambiguous branches such as:

```text
test
new
changes
fixes
darian-work
jaco-work
```

Branches describe the **work**, not the person.

### 4.3 Workstream Independence

Where possible, workstreams should be structured so that developers can work independently.

```text
                    Shared Contracts
                          │
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
          Workstream A Workstream B Workstream C
              │           │           │
              └───────────┼───────────┘
                          ▼
                     Integration
                          │
                          ▼
                         main
```

A developer should not wait for unrelated work to finish if the required interface is already stable.

Where an interface is not yet implemented, the team should agree the contract first and allow parallel implementation against that contract where practical.

### 4.4 Shared Contract Rule

Before implementing a feature that crosses workstreams, identify:

- API contract
- Database contract
- Domain objects
- Permissions
- Events or integration points
- Frontend/backend boundary
- Existing consumers
- Test requirements

Shared contracts should be agreed before parallel implementation begins.

### 4.5 Database Changes

All database changes must use migrations.

A migration must:

- Have a unique sequence number.
- Describe the purpose of the change.
- Be safe to apply to a clean database.
- Preserve existing data where required.
- Avoid destructive changes unless explicitly approved.
- Have corresponding application/test coverage.

Database changes affecting existing modules require additional coordination.

### 4.6 Frontend Changes

Frontend work must consume established API contracts rather than embedding business logic that belongs in the backend.

Frontend implementation should maintain:

- Clear loading states
- Validation feedback
- Error handling
- Permission-aware behaviour
- Consistent API client usage
- Automated verification where practical

### 4.7 Testing Strategy

Testing should operate at multiple levels:

```text
Unit tests
    ↓
Application/service tests
    ↓
HTTP/API tests
    ↓
Integration tests
    ↓
Full regression suite
```

Critical business operations require automated tests for:

- Successful operation
- Validation failure
- Authorisation failure
- Duplicate/conflicting data
- Transaction failure
- Relevant edge cases

### 4.8 Safe Next-Work Rule

Before starting work, the developer should answer:

1. What requirement am I implementing?
2. Which workstream owns it?
3. What existing code will I modify?
4. Which shared contracts will be affected?
5. What dependencies must already exist?
6. What tests prove that the change works?
7. What must remain untouched?

If any answer is unclear and the change affects shared architecture, development should pause until the boundary is clarified.

### 4.9 Darian's Technical Starting Point

Darian should begin technical development from the verified `main` baseline rather than from an independent copy or historical branch.

Initial onboarding sequence:

```text
Synchronise repository
        ↓
Read BETA_TECHNICAL_HANDOVER.md
        ↓
Review current architecture
        ↓
Review latest daily status
        ↓
Run existing tests
        ↓
Verify local environment
        ↓
Select assigned workstream
        ↓
Create feature branch
        ↓
Implement
```

Darian should not immediately refactor existing modules simply to become familiar with the codebase.

Codebase familiarity should initially be gained through:

- Reading existing implementation
- Running tests
- Tracing existing workflows
- Reviewing Git history
- Reviewing architecture documentation
- Implementing an approved work item

### 4.10 Current Safe Development Boundary

Until the complete Beta workstream map is explicitly recorded, the following are protected:

- Customer Master completed workflow
- Existing Production 360 functionality
- Existing System Platform foundations
- Existing RBAC architecture
- Existing repository structure
- Existing database architecture

New functionality may be added around these boundaries where it does not break established contracts.

### 4.11 Beta Execution Backlog

The implementation sequence should follow the agreed Beta backlog in Method §3.25.

Darian's first implementation package must be one bounded Production 360-required Company Platform data capability. It should include:

1. Existing-code review for the selected capability.
2. Requirement and data-contract confirmation with Jaco.
3. Database changes, if required.
4. Application/service implementation.
5. API implementation.
6. Frontend implementation where required.
7. Automated tests.
8. Integration verification against the Production 360 requirement.
9. Git checkpoint.
10. Update to `docs/BETA_TECHNICAL_HANDOVER.md` and the daily status record.

Do not start Sage, Documents, Connect or AI implementation ahead of the first master-data capability unless an explicit dependency review shows that doing so is useful and the scope is agreed.

### 4.12 Jaco Support Model

Jaco is available as an active product and architectural support resource.

Darian should ask for assistance when:

- Phoenix domain context is unclear.
- A Production 360 dependency is unclear.
- A business rule has not been explicitly defined.
- A shared interface needs a decision.
- Existing behaviour appears inconsistent with the intended product behaviour.
- A change could affect another active workstream.

The preferred response is a short joint decision followed by Darian continuing the implementation.

The objective is to avoid both extremes:

- Darian being blocked because he lacks historical/product context.
- Jaco taking over implementation unnecessarily and creating overlapping ownership.

---

## Milestones

Milestones are used to track progression toward the first official Phoenix Core release.

### Milestone 1 — Versioning Baseline

**Status:** Complete

Deliverables:

- Phoenix Core development version established as `v1.0.0-alpha.1`
- Active project version references updated
- Historical migration references preserved
- Frontend build verified
- Versioning changes merged to `main`

Git checkpoint:

```text
601c919
```

### Milestone 2 — Technical Handover

**Status:** In progress

Deliverables:

- Live Beta Technical Handover
- Development rules
- Ownership model
- Workstream boundaries
- Current technical baseline
- Known issues
- Safe-next-work guidance

### Milestone 3 — Beta Workstream Definition

**Status:** Pending

Deliverables:

- Complete approved Beta scope
- Workstream decomposition
- Dependencies
- Technical owners
- Acceptance criteria
- Priority ordering
- Parallel development boundaries

### Milestone 4 — Beta Implementation

**Status:** Pending

Deliverables:

- Approved Beta functionality implemented
- Automated tests
- API and database contracts documented
- Cross-module integration verified
- Known defects tracked

### Milestone 5 — Beta Stabilisation

**Status:** Pending

Deliverables:

- Regression testing
- Critical defect resolution
- Performance verification
- Security verification
- Deployment verification
- Documentation completion

### Milestone 6 — Release Candidate

**Status:** Pending

Target version:

`v1.0.0-rc.1`

Deliverables:

- Release candidate build
- Production deployment verification
- Final acceptance testing
- Release-blocking defects resolved

### Milestone 7 — Phoenix Core v1.0.0

**Status:** Pending

The first official Phoenix Core release will be:

`v1.0.0`

---

## Gathering Results

Phoenix Core Beta readiness will be evaluated against measurable technical and product outcomes.

### 6.1 Functional Results

Each Must Have requirement must have evidence of completion.

Evidence may include:

- Automated tests
- API tests
- UI verification
- Database verification
- Acceptance testing
- Git checkpoints
- Deployment verification

### 6.2 Test Results

At minimum, the release process must record:

```text
Unit test result
Application test result
HTTP/API test result
Integration test result
Full regression result
```

Known baseline failures must remain explicitly identified until resolved.

### 6.3 Performance Results

Critical workflows should be evaluated for:

- Response time
- Database performance
- Import/processing duration
- Resource consumption
- Large-data behaviour

Performance targets should be defined for each critical workflow before final release.

### 6.4 Reliability Results

Critical business operations must demonstrate:

- Correct transaction behaviour
- Safe failure
- No unintended partial writes
- Repeatable processing where applicable
- Appropriate error handling

### 6.5 Security Results

Before release, the system must be reviewed for:

- Authentication
- Authorisation
- Permission enforcement
- Input validation
- File-upload security
- Data isolation between organisations
- Sensitive-data handling
- Secure session behaviour

### 6.6 Release Readiness Checklist

Before `v1.0.0`, confirm:

- [ ] All Must Have requirements completed
- [ ] Critical Should Have requirements completed or explicitly accepted
- [ ] No unresolved release-blocking defects
- [ ] Database migrations verified
- [ ] API contracts verified
- [ ] Critical workflows tested
- [ ] Permissions verified
- [ ] Production configuration verified
- [ ] Backup/recovery approach verified
- [ ] Deployment process verified
- [ ] Technical documentation current
- [ ] Product acceptance completed
- [ ] Release candidate successfully deployed
- [ ] Final Git checkpoint created
- [ ] Version tagged as `v1.0.0`

### 6.7 Daily Development Status

At the end of each meaningful development day, a status document should be created:

```text
docs/status/YYYY-MM-DD.md
```

The daily status must contain:

```text
Date
Developer(s)
Branch
Starting Git checkpoint
Ending Git checkpoint

Completed
In progress
Tests executed
Test results
Known issues
Decisions made
Unfinished work
Dependencies
Next actions
Safe next workstream
```

The daily status provides historical traceability while this document remains the current-state technical control point.

### 6.8 Definition of Done

A feature is not considered complete merely because the code exists.

A feature is considered complete when:

1. The approved requirement is implemented.
2. Acceptance criteria are satisfied.
3. Appropriate automated tests pass.
4. Database/API contracts are stable.
5. Authorisation is verified.
6. No known unintended regression exists.
7. The work has a Git checkpoint.
8. The technical handover is updated.
9. Any unfinished work is explicitly recorded.
10. The next developer can understand what changed and what remains.

---

## Current State

### Current Git Baseline

```text
Branch: main
Commit: 601c919
Status: Clean
Remote: origin/main
```

### Product Version

```text
Phoenix Core v1.0.0-alpha.1
```

### Target Release

```text
Phoenix Core v1.0.0
```

### Verified Completed Feature

```text
Customer Master Import
```

### Current Technical Direction

The agreed Beta model is parallel implementation with coordinated architectural decisions. Darian leads bounded Company Platform implementation; Jaco continues Production 360 and product/architectural direction. Company Platform remains the authoritative owner of Core/master data, while Production 360 owns production-specific operations.

The Beta architecture accepts that Production 360 is currently incorporated into the Core application. The final release target is a modular architecture in which Production 360 and future modules are standalone and access Core through controlled gates/interfaces.

```text
Stabilise foundation
        ↓
Define Beta workstreams
        ↓
Implement approved Beta scope
        ↓
Integrate
        ↓
Stabilise
        ↓
Release Candidate
        ↓
v1.0.0
```

### Immediate Next Actions

1. Treat `192af5a` as the current published handover checkpoint.
2. Confirm the approved parallel-development and Company Platform ↔ Production 360 boundary.
3. Identify the next Production 360-required Company Platform data capability after Customer Master.
4. Jaco and Darian agree the requirement/data contract for that capability.
5. Darian implements that one bounded capability end-to-end.
6. Record the work in the daily status document and create a Git checkpoint.
7. Continue through the Company Platform Beta backlog one bounded capability at a time.
8. Use joint decision gates for shared architecture, contracts and material scope changes.
---

## Document Control

| Version | Date | Change | Status |
|---|---|---|---|
| v0.1 | 2026-10-06 | Initial Beta Technical Handover | Active |

This document is a living technical control document and must be updated whenever the current development state materially changes.

---

## Need Professional Help in Developing Your Architecture?

Please contact me at [sammuti.com](https://sammuti.com) :)
