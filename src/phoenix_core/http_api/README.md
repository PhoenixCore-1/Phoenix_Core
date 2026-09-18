# Phoenix Core HTTP API

This package is the HTTP transport adapter for Phoenix Core.

## Authority

The adapter does not own authentication, tenancy, permissions, module
entitlements, audit, or business data. Those remain authoritative in Phoenix
Core application services.

## Request context

Authenticated routes resolve a Core `RequestContext` from the server-side
session and organisation membership. Browser-supplied identity IDs,
permission lists, and entitlement lists are never trusted.

## Authorization

Use `require_permission(...)` or `require_entitlement(...)` at the HTTP
boundary for routes that require authorization. The resolved Core context is
stored on `request.state.core_context` for the duration of the request.

## Session transport

The browser receives the opaque session credential in an `HttpOnly` secure
cookie. The credential is not returned in the login JSON response.
