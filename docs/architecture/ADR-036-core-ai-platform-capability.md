# ADR-036 — Core AI Platform Capability

**Status:** Accepted  
**Date:** 2026-09-03  
**Decision:** AI is a Core-level Phoenix platform capability.

## Context

Phoenix will contain multiple independent business modules that will increasingly require AI capabilities.

If each module implements its own AI provider integration, authentication, security, context handling, usage tracking, governance, and audit, Phoenix would develop multiple competing AI infrastructures and inconsistent security boundaries.

Phoenix Core already provides the authoritative foundations for identity, organisation/tenant isolation, permissions, entitlements, audit, APIs, background jobs, and other cross-platform capabilities.

AI therefore belongs at the Core platform level.

## Decision

Phoenix Core V2 shall provide one authoritative, provider-independent AI services layer.

Core AI provides the generic AI infrastructure and governance required by Phoenix and its modules.

Generic AI capabilities include:

- ask
- summarize
- extract
- recommend
- classify
- predict
- detect
- generate
- propose authorized actions
- execute authorized actions

The exact capabilities exposed by Core may expand through controlled Core extension points without requiring a competing AI authority or a Core rebuild.

## Authority Boundary

AI is not a source-of-truth authority.

AI may interpret information, generate content, make recommendations, identify patterns, predict outcomes, or propose actions.

AI must not directly become the authority over Phoenix business state.

When an AI operation proposes or executes a business action:

```text
AI
 ↓
Proposal / Action Request
 ↓
Core authorization
 ↓
Owning module application service
 ↓
Business validation
 ↓
Transaction
 ↓
Audit