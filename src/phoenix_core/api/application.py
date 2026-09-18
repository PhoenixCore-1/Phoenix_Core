"""Framework-independent Phoenix Core API application boundary."""

from uuid import UUID

from phoenix_core.api.context import RequestContextResolver
from phoenix_core.api.contracts import ApiResponse
from phoenix_core.audit.domain import AuditEvent
from phoenix_core.auth.service import AuthenticationService
from phoenix_core.errors import AuthorizationError


class CoreApi:
    """Authoritative application-facing API boundary for Phoenix Core."""

    def __init__(self, db, core_service):
        self.db = db
        self.core_service = core_service
        self.authentication_service = AuthenticationService(db)
        self.context_resolver = RequestContextResolver(db, core_service)

    def resolve_context(self, *, request_id: str, session_id, organisation_id=None):
        return self.context_resolver.resolve(request_id=request_id, session_id=session_id, organisation_id=organisation_id)

    def resolve_session_id(self, token: str):
        """Resolve an opaque browser session credential to its Core session ID."""
        return self.authentication_service.resolve_session_id(token)

    @staticmethod
    def require_permission(context, permission: str) -> None:
        if not context.has_permission(permission):
            raise AuthorizationError("Permission denied.")

    @staticmethod
    def require_entitlement(context, module_code: str) -> None:
        if not context.has_entitlement(module_code):
            raise AuthorizationError("Module entitlement required.")

    def authenticate(self, *, request_id: str, username: str, password: str, organisation_id=None) -> ApiResponse:
        session, token = self.authentication_service.authenticate(username, password, organisation_id)
        return ApiResponse(data={
            "session_id": str(session.id), "identity_id": str(session.identity_id), "token": token,
            "status": session.status, "expires_at": session.expires_at.isoformat(),
        }, request_id=request_id)

    def revoke_session(self, *, request_id: str, token: str) -> ApiResponse:
        revoked = self.core_service.revoke_session(token)
        return ApiResponse(data={"revoked": revoked}, request_id=request_id)

    def get_current_identity(self, *, request_id: str, session_id, organisation_id=None) -> ApiResponse:
        context = self.resolve_context(request_id=request_id, session_id=session_id, organisation_id=organisation_id)
        identity = self.core_service.get_identity(context.identity_id)
        return ApiResponse(data={"id": str(identity.id), "type": identity.identity_type, "status": identity.status}, request_id=context.request_id)

    def get_current_organisation(self, *, request_id: str, session_id, organisation_id=None) -> ApiResponse:
        context = self.resolve_context(request_id=request_id, session_id=session_id, organisation_id=organisation_id)
        organisation = self.core_service.get_organisation(context.organisation_id)
        return ApiResponse(data={
            "id": str(organisation.id), "code": organisation.code, "name": organisation.name,
            "status": organisation.status, "created_at": organisation.created_at.isoformat(),
        }, request_id=context.request_id)

    def get_current_user(self, *, request_id: str, session_id, organisation_id=None) -> ApiResponse:
        context = self.resolve_context(request_id=request_id, session_id=session_id, organisation_id=organisation_id)
        user = self.core_service.get_user_by_identity(context.identity_id)
        return ApiResponse(data={
            "id": str(user.id), "identity_id": str(user.identity_id), "username": user.username,
            "display_name": user.display_name, "status": user.status, "created_at": user.created_at.isoformat(),
        }, request_id=context.request_id)

    def get_company_activity(self, context, *, action=None, target_type=None, identity_id=None, limit=100, offset=0) -> ApiResponse:
        """Read tenant-scoped Core audit activity for Company Platform oversight."""
        self.require_permission(context, "company.activity.view")
        if identity_id is not None:
            memberships = self.core_service.list_memberships(context.organisation_id)
            if not any(item.identity_id == identity_id and item.status != "REMOVED" for item in memberships):
                raise AuthorizationError("Activity identity does not belong to the current organisation.")
        events = self.core_service.audit_service.list(
            organisation_id=context.organisation_id,
            identity_id=identity_id,
            action=action,
            target_type=target_type,
            limit=limit,
            offset=offset,
        )
        return ApiResponse(data={
            "items": [{
                "id": str(event.id),
                "organisation_id": str(event.organisation_id) if event.organisation_id else None,
                "identity_id": str(event.identity_id) if event.identity_id else None,
                "action": event.action,
                "target_type": event.target_type,
                "target_id": str(event.target_id) if event.target_id else None,
                "request_id": event.request_id,
                "created_at": event.created_at.isoformat(),
            } for event in events],
            "limit": limit,
            "offset": offset,
        }, request_id=context.request_id)

    def _audit(self, context, *, action: str, target_type: str, target_id: UUID | None = None) -> None:
        self.core_service.audit_service.record(AuditEvent.create(
            action=action,
            organisation_id=context.organisation_id,
            identity_id=context.identity_id,
            target_type=target_type,
            target_id=target_id,
            request_id=context.request_id,
        ))

    def company_create_user(self, context, *, username: str, display_name: str, password: str) -> ApiResponse:
        self.require_permission(context, "company.users.manage")
        user = self.core_service.create_user(username, display_name, password)
        membership = self.core_service.add_membership(user.identity_id, context.organisation_id)
        self._audit(context, action="COMPANY_USER_CREATED", target_type="USER", target_id=user.id)
        self._audit(context, action="COMPANY_MEMBERSHIP_CREATED", target_type="MEMBERSHIP", target_id=membership.id)
        return ApiResponse(data={
            "user": {"id": str(user.id), "identity_id": str(user.identity_id), "username": user.username,
                     "display_name": user.display_name, "status": user.status},
            "membership": {"id": str(membership.id), "status": membership.status},
        }, request_id=context.request_id)

    def company_update_user(self, context, user_id: UUID, *, username: str | None = None, display_name: str | None = None) -> ApiResponse:
        self.require_permission(context, "company.users.manage")
        user = self.core_service.get_user(user_id)
        memberships = self.core_service.list_memberships(context.organisation_id)
        if not any(item.identity_id == user.identity_id and item.status != "REMOVED" for item in memberships):
            raise AuthorizationError("User does not belong to the current organisation.")
        updated = self.core_service.update_user(user_id, username=username, display_name=display_name)
        self._audit(context, action="COMPANY_USER_UPDATED", target_type="USER", target_id=updated.id)
        return ApiResponse(data={
            "id": str(updated.id), "identity_id": str(updated.identity_id), "username": updated.username,
            "display_name": updated.display_name, "status": updated.status,
        }, request_id=context.request_id)

    def company_set_membership_status(self, context, membership_id: UUID, status: str) -> ApiResponse:
        self.require_permission(context, "company.memberships.manage")
        membership = self.core_service.get_membership(membership_id)
        if membership.organisation_id != context.organisation_id:
            raise AuthorizationError("Membership does not belong to the current organisation.")
        updated = self.core_service.set_membership_status(membership_id, status)
        self._audit(context, action=f"COMPANY_MEMBERSHIP_{status}", target_type="MEMBERSHIP", target_id=updated.id)
        return ApiResponse(data={
            "id": str(updated.id), "identity_id": str(updated.identity_id), "organisation_id": str(updated.organisation_id),
            "status": updated.status, "created_at": updated.created_at.isoformat(),
        }, request_id=context.request_id)

    def company_create_role(self, context, *, code: str, name: str) -> ApiResponse:
        self.require_permission(context, "company.roles.manage")
        role = self.core_service.create_role(context.organisation_id, code, name)
        self._audit(context, action="COMPANY_ROLE_CREATED", target_type="ROLE", target_id=role.id)
        return ApiResponse(data={"id": str(role.id), "organisation_id": str(role.organisation_id), "code": role.code,
                                 "name": role.name, "scope": role.scope, "status": role.status}, request_id=context.request_id)

    def company_update_role(self, context, role_id: UUID, *, code: str | None = None, name: str | None = None) -> ApiResponse:
        self.require_permission(context, "company.roles.manage")
        role = self.core_service.get_role(role_id)
        if role.organisation_id != context.organisation_id:
            raise AuthorizationError("Role does not belong to the current organisation.")
        updated = self.core_service.update_role(role_id, code=code, name=name)
        self._audit(context, action="COMPANY_ROLE_UPDATED", target_type="ROLE", target_id=updated.id)
        return ApiResponse(data={"id": str(updated.id), "organisation_id": str(updated.organisation_id), "code": updated.code,
                                 "name": updated.name, "scope": updated.scope, "status": updated.status}, request_id=context.request_id)

    def company_set_role_status(self, context, role_id: UUID, status: str) -> ApiResponse:
        self.require_permission(context, "company.roles.manage")
        role = self.core_service.get_role(role_id)
        if role.organisation_id != context.organisation_id:
            raise AuthorizationError("Role does not belong to the current organisation.")
        updated = self.core_service.set_role_status(role_id, status)
        self._audit(context, action=f"COMPANY_ROLE_{status}", target_type="ROLE", target_id=updated.id)
        return ApiResponse(data={"id": str(updated.id), "organisation_id": str(updated.organisation_id), "code": updated.code,
                                 "name": updated.name, "scope": updated.scope, "status": updated.status}, request_id=context.request_id)

    def company_assign_role(self, context, membership_id: UUID, role_id: UUID) -> ApiResponse:
        self.require_permission(context, "company.roles.manage")
        membership = self.core_service.get_membership(membership_id)
        role = self.core_service.get_role(role_id)
        if membership.organisation_id != context.organisation_id or role.organisation_id != context.organisation_id:
            raise AuthorizationError("Role and membership must belong to the current organisation.")
        assignment_id = self.core_service.assign_role(membership_id, role_id)
        self._audit(context, action="COMPANY_ROLE_ASSIGNED", target_type="ROLE_ASSIGNMENT", target_id=UUID(assignment_id))
        return ApiResponse(data={"id": assignment_id, "membership_id": str(membership_id), "role_id": str(role_id)}, request_id=context.request_id)

    def company_remove_role(self, context, membership_id: UUID, role_id: UUID) -> ApiResponse:
        self.require_permission(context, "company.roles.manage")
        membership = self.core_service.get_membership(membership_id)
        role = self.core_service.get_role(role_id)
        if membership.organisation_id != context.organisation_id or role.organisation_id != context.organisation_id:
            raise AuthorizationError("Role and membership must belong to the current organisation.")
        removed = self.core_service.remove_role(membership_id, role_id)
        if removed:
            self._audit(context, action="COMPANY_ROLE_REMOVED", target_type="ROLE", target_id=role_id)
        return ApiResponse(data={"removed": removed, "membership_id": str(membership_id), "role_id": str(role_id)}, request_id=context.request_id)

    def company_grant_permission(self, context, role_id: UUID, permission_id: UUID) -> ApiResponse:
        self.require_permission(context, "company.roles.manage")
        role = self.core_service.get_role(role_id)
        if role.organisation_id != context.organisation_id:
            raise AuthorizationError("Role does not belong to the current organisation.")
        self.core_service.grant_permission(role_id, permission_id)
        self._audit(context, action="COMPANY_ROLE_PERMISSION_GRANTED", target_type="ROLE", target_id=role_id)
        return ApiResponse(data={"granted": True, "role_id": str(role_id), "permission_id": str(permission_id)}, request_id=context.request_id)

    def company_revoke_permission(self, context, role_id: UUID, permission_id: UUID) -> ApiResponse:
        self.require_permission(context, "company.roles.manage")
        role = self.core_service.get_role(role_id)
        if role.organisation_id != context.organisation_id:
            raise AuthorizationError("Role does not belong to the current organisation.")
        removed = self.core_service.revoke_permission(role_id, permission_id)
        if removed:
            self._audit(context, action="COMPANY_ROLE_PERMISSION_REVOKED", target_type="ROLE", target_id=role_id)
        return ApiResponse(data={"revoked": removed, "role_id": str(role_id), "permission_id": str(permission_id)}, request_id=context.request_id)
