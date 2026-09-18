# ADR-041: Phoenix IP, Provenance & Clean-Room Development

## Status

Accepted

## Date

2026-09-04

## Decision

Phoenix must be developed as an independently authored software platform from Phoenix requirements, architecture decisions, implementation decisions, tests, and documented business needs.

Phoenix may use general industry-standard software engineering patterns, practices, algorithms, architectural concepts, and appropriately licensed third-party/open-source components.

Phoenix must not intentionally copy, reproduce, adapt, or incorporate proprietary third-party implementation material without appropriate authorization or licensing.

This decision applies to Phoenix Core, Phoenix Generic Framework, Phoenix System, Phoenix Platform UI, business modules, integrations, documentation, AI capabilities, prompts, workflows, and future Phoenix components.

## Purpose

The purpose of this ADR is to establish a permanent provenance and intellectual-property discipline for Phoenix so that the platform can be developed, maintained, commercialised, and extended without creating avoidable claims that Phoenix copied another system's protected implementation.

The rule is preventive rather than corrective.

Phoenix should establish clean provenance at the time material is introduced instead of attempting to determine or remove questionable material later.

## 1. Independent Phoenix Development

Phoenix implementation must originate from one or more of:

- Phoenix product requirements;
- Phoenix business requirements;
- Phoenix architecture decisions;
- Phoenix ADRs;
- Phoenix domain models;
- Phoenix technical design decisions;
- independently developed implementation;
- independently developed tests;
- authorised customer or business requirements;
- appropriately licensed third-party components.

Phoenix architecture and implementation must not be intentionally derived by copying another system's proprietary implementation.

## 2. Permitted General Engineering Patterns

Phoenix may independently use broadly established software engineering concepts and patterns.

Examples include:

- layered architecture;
- domain/service separation;
- dependency injection;
- interfaces and contracts;
- modular architecture;
- RBAC;
- tenant isolation;
- database migrations;
- transactions;
- command/query separation;
- events and messaging;
- background jobs;
- API versioning;
- provider abstraction;
- audit logging;
- caching;
- read models;
- feature flags;
- subscription and entitlement concepts;
- standard security controls.

The existence of similar concepts in other systems does not by itself constitute copying.

Phoenix may independently arrive at similar architectural solutions where those solutions are based on Phoenix requirements and engineering reasoning.

## 3. Prohibited Proprietary Material

Without appropriate authorization or licensing, Phoenix must not incorporate or reproduce:

- proprietary source code;
- proprietary database schemas or database designs copied from another implementation;
- proprietary API implementations;
- proprietary algorithms or implementation details;
- proprietary documentation;
- proprietary UI designs or distinctive copied screen layouts;
- proprietary workflows copied from another product;
- proprietary business rules;
- proprietary prompts or prompt libraries;
- proprietary data models copied from another implementation;
- proprietary configuration or deployment artifacts;
- proprietary test suites or copied test cases;
- proprietary internal terminology where its use is part of protected/confidential material;
- confidential technical information;
- trade secrets;
- copied or substantially reproduced protected content.

Renaming, restructuring, translating, or lightly modifying proprietary material does not make it independently authored.

## 4. Competitor and Existing-System Research

Research into existing systems, competitors, customer systems, or industry products may be used to understand:

- business problems;
- market expectations;
- interoperability requirements;
- generally available product capabilities;
- user needs;
- functional requirements;
- industry conventions.

Research must not become a mechanism for copying proprietary implementation.

Phoenix requirements should be expressed in Phoenix terms and implemented independently.

Where a requirement can be satisfied independently, Phoenix should prefer independent design rather than reproducing a distinctive implementation unnecessarily.

## 5. Existing Upat Systems and Material

Existing Upat systems, applications, databases, documents, workflows, and technical material are not automatically Phoenix IP.

Where existing Upat material is used, its authority and right of use must be clear.

Upat-specific implementation must remain distinguishable from generic Phoenix IP where required by the Phoenix architecture.

Existing systems may provide:

- migration/reference information;
- business requirements;
- lessons learned;
- integration requirements;
- authorised source data;
- authorised domain knowledge.

They must not be treated as permission to copy implementation into Phoenix.

This preserves the existing Phoenix architectural rule that generic Phoenix IP and Upat-specific IP remain appropriately separated.

## 6. Open-Source and Third-Party Components

Phoenix may use third-party and open-source software where its licence permits the intended use.

For each material third-party dependency, Phoenix should maintain provenance information sufficient to identify:

- component name;
- version;
- source;
- licence;
- relevant licence obligations;
- purpose within Phoenix;
- date introduced where practical.

Third-party components must not be copied into Phoenix outside their permitted licence terms.

Dependencies should be preferred over copying implementation when a properly licensed component provides the required capability.

## 7. AI-Assisted Development

AI-assisted development does not change Phoenix provenance requirements.

Code, documentation, tests, prompts, designs, or other material generated or assisted by AI must be treated as Phoenix implementation and reviewed under the same provenance rules.

AI-generated output must not be intentionally used to reproduce proprietary third-party implementation.

Where AI-assisted output materially incorporates known third-party material, the relevant provenance and licence must be established before incorporation.

AI is an implementation aid and is not a substitute for Phoenix architecture, engineering, security, licensing, or provenance review.

## 8. Phoenix Provenance Chain

Material introduced into Phoenix should be traceable where practical through the development chain:

Requirements
    |
    v
Architecture / ADR
    |
    v
Technical Design
    |
    v
Implementation
    |
    v
Tests
    |
    v
Git Commit
    |
    v
Release

This provides an auditable history showing why and how Phoenix capabilities were developed.

## 9. Architecture and Implementation Review Gate

Before incorporating material originating outside Phoenix, the following questions must be considered:

1. What is the source?
2. Do we have the right to use it?
3. Is it proprietary, confidential, or restricted?
4. What licence or authorization applies?
5. Are we using a general concept or reproducing a specific implementation?
6. Can Phoenix implement the requirement independently?
7. Does the material contain third-party code, documentation, designs, schemas, workflows, prompts, or other protected content?
8. Does incorporation create a conflict with Phoenix's generic-IP / customer-specific-IP boundary?
9. Can provenance and applicable licence/authorization be recorded?

If provenance or usage rights are unclear, the material must not be incorporated into Phoenix until the issue is resolved.

## 10. Architecture Decision Provenance

Phoenix ADRs are authoritative records of Phoenix architectural decisions.

An ADR should explain the Phoenix reason for a material architectural decision and should not be used to reproduce another system's proprietary design documentation.

Where Phoenix independently adopts a common industry pattern, the ADR should describe the Phoenix requirement and rationale rather than presenting the design as copied from another implementation.

## 11. Code and Documentation Provenance

Phoenix source code, tests, documentation, migrations, configuration, and deployment artefacts should be developed within the Phoenix development environment and tracked through the Phoenix repository.

Generated, temporary, migration, legacy, or reference material must remain separated according to the Phoenix lifecycle and repository rules.

Copied external material must not be placed into authoritative Phoenix source locations merely for convenience.

## 12. No Retroactive Cleanup as a Development Strategy

Phoenix development must not rely on:

"Build first, determine provenance later."

Potentially questionable material must be identified before incorporation where reasonably possible.

If provenance later becomes uncertain, the material must be isolated and reviewed before it becomes part of an authoritative Phoenix release.

## 13. Relationship to Phoenix V2 Authority

This ADR does not create another architectural authority.

It applies across:

- Phoenix Core;
- Phoenix Generic Framework;
- Phoenix System;
- Phoenix Platform;
- module integration;
- business modules;
- external integrations;
- AI services;
- deployment and supporting tooling.

Existing authority and ownership ADRs remain authoritative for their respective technical domains.

This ADR governs the provenance and development discipline applied to those domains.

## 14. V2.0 Scope

This ADR is a V2.0 architectural governance requirement.

V2.0 requires sufficient provenance discipline to ensure that its implementation is independently developed and that incorporated third-party components have appropriate usage rights.

A future V3.0 may introduce more formal software asset management, automated software composition analysis, licence scanning, legal review workflows, supplier provenance management, or broader governance capabilities.

Those future capabilities do not remove the V2.0 requirement to maintain clean development provenance.

## 15. Consequences

### Positive

- Reduces risk of accidental proprietary-material incorporation.
- Creates a defensible development history.
- Preserves separation between Phoenix IP and customer-specific material.
- Makes third-party dependency use more transparent.
- Supports future commercialisation and licensing review.
- Prevents provenance concerns from becoming a late-stage cleanup exercise.
- Reinforces independent Phoenix architecture.

### Negative

- Requires additional discipline when incorporating external material.
- Third-party dependencies require licence/provenance tracking.
- Some useful external material may need to be independently reimplemented.
- Unclear-source material may have to be excluded until reviewed.

These costs are accepted because clean provenance is more important than short-term implementation convenience.

## 16. Guiding Principle

> **Phoenix may learn from the industry, but Phoenix must build its own system.**

Use established engineering knowledge.

Use properly licensed components.

Use authorised business requirements.

Learn from previous Phoenix versions.

But do not copy another system's protected implementation into Phoenix.

## 17. Architectural Status

ADR-041 is accepted and authoritative for Phoenix V2 development.

It applies immediately to all new Phoenix work and to future extensions of the V2 architecture.
