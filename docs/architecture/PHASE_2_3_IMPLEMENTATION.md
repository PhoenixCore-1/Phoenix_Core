# Phoenix Core V2 — Phase 2.3 Implementation

Phase 2.3 implements the Core RBAC foundation: organisation-scoped roles, globally registered permissions, role assignments, role-permission grants, and effective authorization.

Rules:
- Roles are organisation-scoped in this phase.
- System roles are reserved for Phoenix System administration and cannot be created through tenant role services.
- Permission codes are globally unique and normalized to lowercase.
- Role codes are unique within an organisation and normalized to uppercase.
- A role assignment requires an active membership and active role in the same organisation.
- Disabled roles do not contribute effective permissions.
- Effective authorization requires an active membership and active organisation.
- Role and permission administration remains Core authority; business modules consume authorization outcomes.
