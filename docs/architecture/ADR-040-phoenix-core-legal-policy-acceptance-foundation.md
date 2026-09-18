# ADR-040 — Phoenix Core Legal, Policy & Acceptance Foundation

## Status
Accepted

## Date
2026-09-04

## Decision
Phoenix Core V2 will provide the authoritative generic foundation for platform-level legal policies, terms, required acceptance and acceptance status.

This capability is part of Phoenix Core V2.0 and is intentionally limited to the legal and policy requirements required to operate Phoenix V2.0.

It is not a general regulatory-compliance platform and does not include ERP, SARS, tax or other V3.0 compliance requirements.

## 1. Purpose

Phoenix requires a consistent platform-level mechanism for managing legal and policy requirements that can affect access to the Phoenix platform.

Examples include:

- Phoenix EULA / Terms of Service
- Privacy Policy where required
- Acceptable Use Policy where required
- Other mandatory Phoenix platform policies

The architecture must provide a single authoritative mechanism for:

- Policy identity
- Policy type
- Policy version
- Effective dates
- Active/inactive status
- Acceptance requirements
- Acceptance records
- Acceptance status
- Access enforcement
- Auditability

Business modules must not create competing platform-wide legal or acceptance authorities.

## 2. Core Authority

Phoenix Core is authoritative for the platform-level policy and acceptance state.

Core owns:

- Policy identity
- Policy type
- Policy version
- Policy lifecycle/status
- Effective dates
- Acceptance requirements
- Acceptance records
- Acceptance status
- Platform access enforcement related to required policies
- Tenant/user ownership of acceptance records
- Integration with the authoritative Core Audit service

Core does not own the legal meaning of the policies.

The legal/commercial content remains controlled by the appropriate Phoenix business, legal or commercial process.

## 3. Document Authority

Policy documents must use the existing Phoenix Core Files, Documents & Attachments authority defined by ADR-034.

Core Documents remains authoritative for:

- Document metadata
- Tenant ownership
- Access enforcement
- Document lifecycle
- Storage abstraction
- Attachment relationships
- Document audit integration

Legal and policy functionality must not create a second document storage or attachment authority.

A policy may therefore reference an authoritative Core document representing the applicable policy content.

## 4. Policy Model

A platform policy must be represented as an authoritative policy record.

At minimum, the policy model must support:

- Policy identifier
- Policy type
- Version
- Status
- Effective-from date/time
- Effective-until date/time where applicable
- Required acceptance flag
- Document reference
- Applicable scope
- Metadata

Policy versions are immutable once they have been used as an acceptance target.

A new legal or policy revision creates a new version rather than silently changing an already accepted version.

## 5. Acceptance Model

Acceptance must be recorded as an explicit platform record.

At minimum, an acceptance record must support:

- Acceptance identifier
- Policy identifier
- Policy version
- Identity/user
- Organisation/tenant where applicable
- Acceptance timestamp
- Request/session context where applicable
- Relevant audit/correlation information

Acceptance must identify the exact policy version accepted.

The platform must never treat acceptance of an older version as automatic acceptance of a newer required version.

## 6. User and Organisation Scope

Phoenix must support acceptance requirements at the appropriate scope.

### User-level acceptance

A policy may require each individual user to accept it.

Example:

- Phoenix EULA

The acceptance belongs to the identity that accepted it.

### Organisation-level acceptance

A policy may require acceptance on behalf of an organisation/tenant where appropriate.

The organisation-level acceptance mechanism must not replace individual acceptance where individual acceptance is legally or operationally required.

The policy definition determines the applicable acceptance scope.

## 7. Access Enforcement

Required policies may participate in platform access enforcement.

The general flow is:

Authentication
    |
Tenant / Organisation Context
    |
Required Policy Evaluation
    |
Acceptance Status
    |
Authorization / Platform Access
    |
Phoenix Platform

If a currently required policy has not been accepted, Phoenix may require acceptance before allowing continued access to protected platform functionality.

Enforcement must use the authoritative Core identity, organisation, authentication, permission and audit authorities.

Policy enforcement must not create a second authentication or authorization system.

## 8. Versioning
## 8. Versioning

Policies are versioned explicitly.

A policy version must remain historically identifiable after it is superseded.

When a new version becomes effective:

- Existing acceptance records remain historical records.
- The new version becomes the current acceptance target where required.
- Users or organisations may be required to accept the new version.
- Previous acceptance must not be rewritten or deleted to represent the new acceptance.

This preserves a defensible historical record.

## 9. Audit

Policy creation, publication, acceptance, supersession and relevant enforcement actions must integrate with the existing Phoenix Core Audit authority.

The existing Core Audit service remains the single authoritative audit mechanism.

Legal/policy functionality must not create a competing global audit log.

Where applicable, audit information should identify:

- Policy
- Version
- Identity
- Organisation/tenant
- Action
- Timestamp
- Request correlation
- Session context

## 10. Tenant Isolation

Policy and acceptance records must respect Phoenix tenant isolation.

Tenant-specific acceptance records must never be visible or usable by another tenant.

Platform-wide policies may be shared as definitions where appropriate, but acceptance state remains correctly scoped to the identity and/or organisation to which it applies.

No policy mechanism may provide a path around Core tenant isolation.

## 11. Security

Policy documents and acceptance records must use the existing Core security model.

Access must be controlled through:

- Authentication
- Tenant context
- Authorization
- Permissions
- Existing document access controls
- Existing Core audit mechanisms

Legal/policy functionality must not introduce independent security credentials or access authorities.

## 12. Commercial Boundary

Commercial terms and subscription agreements may be managed by Phoenix System's commercial/billing capabilities.

However, where a commercial agreement creates a platform entitlement or access requirement, the resulting platform state must use the authoritative Core entitlement and security mechanisms.

The architecture therefore distinguishes:

Commercial agreement
    |
Subscription / Commercial State
    |
Core Entitlement / Platform State
    |
Platform Access

Billing and commercial authority must not be duplicated inside Core.

## 13. Module Boundary

Business modules may define their own domain-specific policies or legal requirements where genuinely required by their business domain.

However, a module must not create a competing platform-wide EULA, identity acceptance, tenant acceptance or global audit authority.

Where a module requires acceptance of a domain-specific policy, it should use the approved Core policy/acceptance contracts where appropriate.

The module remains authoritative for the business meaning of its domain-specific requirement.

## 14. V2.0 Scope Boundary

This ADR intentionally covers only capabilities required for Phoenix V2.0.

Included:

- Phoenix EULA / Terms acceptance
- Required platform policy management
- Policy versioning
- Acceptance records
- Acceptance status
- Required access enforcement
- Audit integration
- Core document integration
- Tenant/security enforcement

Excluded from V2.0:

- ERP compliance
- SARS integration
- SARS submissions/reporting
- Tax compliance platforms
- VAT automation
- ERP financial compliance
- Broad regulatory compliance frameworks
- Advanced legal contract lifecycle management
- General-purpose governance/risk/compliance platforms

These may be considered for Phoenix V3.0.

## 15. Prohibited Patterns

The following are prohibited:

- Modules creating their own platform-wide EULA authority.
- Duplicate policy acceptance authorities.
- Duplicate global audit authorities.
- Duplicate document storage systems.
- Acceptance records without tenant/identity ownership where applicable.
- Treating one policy version as acceptance of another version.
- Bypassing Core authentication or authorization.
- Bypassing tenant isolation.
- Hard-coding legal policy content into business logic.
- Embedding ERP/SARS compliance into the V2.0 Core.

## 16. Consequences

### Positive

- Phoenix has one authoritative platform policy mechanism.
- EULA and policy acceptance can be enforced consistently.
- Historical acceptance remains traceable.
- Existing Core Documents and Audit authorities are reused.
- Modules remain independent of platform legal infrastructure.
- V2.0 scope remains controlled.
- Future V3.0 compliance capabilities can be added without redefining the V2.0 authority model.

### Negative

- Policy lifecycle and versioning require explicit implementation.
- Acceptance enforcement adds platform access logic.
- Legal content and technical policy state must remain clearly separated.

These costs are intentional because platform-wide legal requirements must not be implemented independently by individual modules.

## 17. Architectural Principle

Phoenix Core owns the authoritative technical state required to enforce Phoenix platform policies.

Core does not become the legal authority.

Core provides the mechanism.

The appropriate legal/commercial authority provides the policy content and business decision.

Core records and enforces the resulting platform state.

## 18. Guiding Principle

V2.0 implements only the legal, policy and acceptance capabilities required to operate Phoenix V2.0.

Future ERP, SARS and broader compliance requirements belong to V3.0 unless explicitly brought into V2.0 scope.



