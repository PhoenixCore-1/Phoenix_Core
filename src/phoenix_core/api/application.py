"""Framework-independent Phoenix Core API application boundary."""

from uuid import UUID

from phoenix_core.api.context import RequestContextResolver
from phoenix_core.api.contracts import ApiResponse
from phoenix_core.audit.domain import AuditEvent
from phoenix_core.auth.service import AuthenticationService
from phoenix_core.errors import AuthorizationError
from phoenix_core.legal_compliance import LegalComplianceService
from phoenix_core.ip import IPOwnershipService
from phoenix_core.users.application import UserApplicationService


class CoreApi:
    """Authoritative application-facing API boundary for Phoenix Core."""

    def __init__(self, db, core_service):
        self.db = db
        self.core_service = core_service
        self.authentication_service = AuthenticationService(db)
        self.context_resolver = RequestContextResolver(db, core_service)
        self.legal_compliance_service = LegalComplianceService(db)
        self.ip_ownership_service = IPOwnershipService(self.db)
        self.user_service = UserApplicationService(self)


    # ------------------------------------------------------------------
    # IP Ownership
    # ------------------------------------------------------------------

    def ip_create_owner(
        self,
        context,
        *,
        owner_type: str,
        name: str,
        description: str | None = None,
    ) -> ApiResponse:
        self.require_permission(context, "system.ip_management.manage")

        owner = self.ip_ownership_service.create_owner(
            owner_type=owner_type,
            name=name,
            description=description,
            organisation_id=context.organisation_id
            if owner_type.upper() == "COMPANY"
            else None,
        )

        self._audit(
            context,
            action="IP_OWNER_CREATED",
            target_type="IP_OWNER",
            target_id=UUID(owner["id"]),
        )

        return ApiResponse(
            data=owner,
            request_id=context.request_id,
        )

    def ip_get_owner(
        self,
        context,
        owner_id: UUID,
    ) -> ApiResponse:
        self.require_permission(context, "system.ip_management.view")

        owner = self.ip_ownership_service.get_owner(
            owner_id,
            organisation_id=context.organisation_id,
        )

        return ApiResponse(
            data=owner,
            request_id=context.request_id,
        )

    def ip_list_owners(
        self,
        context,
        *,
        owner_type: str | None = None,
    ) -> ApiResponse:
        self.require_permission(context, "system.ip_management.view")

        owners = self.ip_ownership_service.list_owners(
            organisation_id=context.organisation_id,
            owner_type=owner_type,
        )

        return ApiResponse(
            data={"items": owners},
            request_id=context.request_id,
        )

    def ip_create_asset(
        self,
        context,
        *,
        owner_id: UUID,
        asset_code: str,
        name: str,
        asset_type: str,
        confidentiality_class: str = "INTERNAL",
        description: str | None = None,
    ) -> ApiResponse:
        self.require_permission(context, "system.ip_management.manage")

        asset = self.ip_ownership_service.create_asset(
            owner_id=owner_id,
            asset_code=asset_code,
            name=name,
            asset_type=asset_type,
            confidentiality_class=confidentiality_class,
            description=description,
            organisation_id=context.organisation_id,
        )

        self._audit(
            context,
            action="IP_ASSET_CREATED",
            target_type="IP_ASSET",
            target_id=UUID(asset["id"]),
        )

        return ApiResponse(
            data=asset,
            request_id=context.request_id,
        )

    def ip_get_asset(
        self,
        context,
        asset_id: UUID,
    ) -> ApiResponse:
        self.require_permission(context, "system.ip_management.view")

        asset = self.ip_ownership_service.get_asset(
            asset_id,
            organisation_id=context.organisation_id,
        )

        return ApiResponse(
            data=asset,
            request_id=context.request_id,
        )

    def ip_list_assets(
        self,
        context,
        *,
        owner_id: UUID | None = None,
        asset_type: str | None = None,
    ) -> ApiResponse:
        self.require_permission(context, "system.ip_management.view")

        assets = self.ip_ownership_service.list_assets(
            organisation_id=context.organisation_id,
            owner_id=owner_id,
            asset_type=asset_type,
        )

        return ApiResponse(
            data={"items": assets},
            request_id=context.request_id,
        )

    def ip_transfer_ownership(
        self,
        context,
        asset_id: UUID,
        *,
        new_owner_id: UUID,
        reason: str | None = None,
        document_id: UUID | None = None,
        document_version_id: UUID | None = None,
    ) -> ApiResponse:
        self.require_permission(context, "system.ip_management.manage")

        result = self.ip_ownership_service.record_ownership_transfer(
            asset_id,
            new_owner_id=new_owner_id,
            organisation_id=context.organisation_id,
            reason=reason,
            document_id=document_id,
            document_version_id=document_version_id,
            created_by_identity_id=context.identity_id,
        )

        self._audit(
            context,
            action="IP_OWNERSHIP_TRANSFERRED",
            target_type="IP_ASSET",
            target_id=asset_id,
        )

        return ApiResponse(
            data=result,
            request_id=context.request_id,
        )


    def ip_create_asset_version(
        self,
        context,
        asset_id: UUID,
        *,
        version_label: str,
        description: str | None = None,
        document_id: UUID | None = None,
        document_version_id: UUID | None = None,
        checksum: str | None = None,
        effective_from: str | None = None,
    ) -> ApiResponse:
        self.require_permission(
            context,
            "system.ip_management.manage",
        )

        version = self.ip_ownership_service.create_asset_version(
            asset_id,
            organisation_id=context.organisation_id,
            version_label=version_label,
            description=description,
            document_id=document_id,
            document_version_id=document_version_id,
            checksum=checksum,
            effective_from=effective_from,
        )

        self._audit(
            context,
            action="IP_ASSET_VERSION_CREATED",
            target_type="IP_ASSET_VERSION",
            target_id=UUID(version["id"]),
        )

        return ApiResponse(
            data=version,
            request_id=context.request_id,
        )

    def ip_get_asset_version(
        self,
        context,
        version_id: UUID,
    ) -> ApiResponse:
        self.require_permission(
            context,
            "system.ip_management.view",
        )

        version = self.ip_ownership_service.get_asset_version(
            version_id,
            organisation_id=context.organisation_id,
        )

        return ApiResponse(
            data=version,
            request_id=context.request_id,
        )

    def ip_list_asset_versions(
        self,
        context,
        asset_id: UUID,
    ) -> ApiResponse:
        self.require_permission(
            context,
            "system.ip_management.view",
        )

        versions = self.ip_ownership_service.list_asset_versions(
            asset_id,
            organisation_id=context.organisation_id,
        )

        return ApiResponse(
            data={"items": versions},
            request_id=context.request_id,
        )

    def ip_retire_asset_version(
        self,
        context,
        version_id: UUID,
        *,
        retired_at: str | None = None,
    ) -> ApiResponse:
        self.require_permission(
            context,
            "system.ip_management.manage",
        )

        version = self.ip_ownership_service.retire_asset_version(
            version_id,
            organisation_id=context.organisation_id,
            retired_at=retired_at,
        )

        self._audit(
            context,
            action="IP_ASSET_VERSION_RETIRED",
            target_type="IP_ASSET_VERSION",
            target_id=UUID(version["id"]),
        )

        return ApiResponse(
            data=version,
            request_id=context.request_id,
        )


    def ip_create_licence(
        self,
        context,
        asset_id: UUID,
        *,
        licence_type: str,
        licence_name: str | None = None,
        licence_version: str | None = None,
        licensor: str | None = None,
        licensee: str | None = None,
        permitted_use: str | None = None,
        restrictions: str | None = None,
        source_url: str | None = None,
        document_id: UUID | None = None,
        document_version_id: UUID | None = None,
        effective_from: str | None = None,
        expires_at: str | None = None,
    ) -> ApiResponse:
        self.require_permission(context, "system.ip_management.manage")

        licence = self.ip_ownership_service.create_licence(
            asset_id,
            licence_type=licence_type,
            organisation_id=context.organisation_id,
            licence_name=licence_name,
            licence_version=licence_version,
            licensor=licensor,
            licensee=licensee,
            permitted_use=permitted_use,
            restrictions=restrictions,
            source_url=source_url,
            document_id=document_id,
            document_version_id=document_version_id,
            effective_from=effective_from,
            expires_at=expires_at,
        )

        self._audit(
            context,
            action="IP_LICENCE_CREATED",
            target_type="IP_LICENCE",
            target_id=UUID(licence["id"]),
        )

        return ApiResponse(
            data=licence,
            request_id=context.request_id,
        )

    def ip_record_assignment(
        self,
        context,
        asset_id: UUID,
        *,
        assignee_owner_id: UUID,
        document_id: UUID,
        document_version_id: UUID,
        assignment_type: str,
        assignor_owner_id: UUID | None = None,
        effective_at: str | None = None,
        expires_at: str | None = None,
        notes: str | None = None,
    ) -> ApiResponse:
        self.require_permission(context, "system.ip_management.manage")

        assignment = self.ip_ownership_service.record_assignment(
            asset_id,
            assignee_owner_id=assignee_owner_id,
            document_id=document_id,
            document_version_id=document_version_id,
            assignment_type=assignment_type,
            organisation_id=context.organisation_id,
            assignor_owner_id=assignor_owner_id,
            effective_at=effective_at,
            expires_at=expires_at,
            notes=notes,
        )

        self._audit(
            context,
            action="IP_ASSIGNMENT_RECORDED",
            target_type="IP_CONTRACTUAL_ASSIGNMENT",
            target_id=UUID(assignment["id"]),
        )

        return ApiResponse(
            data=assignment,
            request_id=context.request_id,
        )

    def ip_create_confidentiality_record(
        self,
        context,
        asset_id: UUID,
        *,
        owner_id: UUID,
        party_name: str,
        confidentiality_type: str,
        document_id: UUID,
        document_version_id: UUID,
        effective_at: str,
        expires_at: str | None = None,
    ) -> ApiResponse:
        self.require_permission(context, "system.ip_management.manage")

        record = self.ip_ownership_service.create_confidentiality_record(
            asset_id,
            owner_id=owner_id,
            party_name=party_name,
            confidentiality_type=confidentiality_type,
            document_id=document_id,
            document_version_id=document_version_id,
            effective_at=effective_at,
            organisation_id=context.organisation_id,
            expires_at=expires_at,
        )

        self._audit(
            context,
            action="IP_CONFIDENTIALITY_RECORDED",
            target_type="IP_CONFIDENTIALITY_RECORD",
            target_id=UUID(record["id"]),
        )

        return ApiResponse(
            data=record,
            request_id=context.request_id,
        )

    def ip_register_third_party_component(
        self,
        context,
        asset_id: UUID,
        *,
        component_name: str,
        component_version: str | None = None,
        supplier: str | None = None,
        licence_id: UUID | None = None,
        source_url: str | None = None,
        usage_notes: str | None = None,
    ) -> ApiResponse:
        self.require_permission(context, "system.ip_management.manage")

        component = self.ip_ownership_service.register_third_party_component(
            asset_id,
            component_name=component_name,
            organisation_id=context.organisation_id,
            component_version=component_version,
            supplier=supplier,
            licence_id=licence_id,
            source_url=source_url,
            usage_notes=usage_notes,
        )

        self._audit(
            context,
            action="IP_THIRD_PARTY_COMPONENT_REGISTERED",
            target_type="IP_THIRD_PARTY_COMPONENT",
            target_id=UUID(component["id"]),
        )

        return ApiResponse(
            data=component,
            request_id=context.request_id,
        )

    def ip_add_asset_document(
        self,
        context,
        asset_id: UUID,
        *,
        document_id: UUID,
        document_version_id: UUID,
        document_role: str,
    ) -> ApiResponse:
        self.require_permission(context, "system.ip_management.manage")

        association = self.ip_ownership_service.add_asset_document(
            asset_id,
            document_id=document_id,
            document_version_id=document_version_id,
            document_role=document_role,
            organisation_id=context.organisation_id,
        )

        self._audit(
            context,
            action="IP_DOCUMENT_ASSOCIATED",
            target_type="IP_ASSET_DOCUMENT",
            target_id=UUID(association["id"]),
        )

        return ApiResponse(
            data=association,
            request_id=context.request_id,
        )

    def ip_list_asset_documents(
        self,
        context,
        asset_id: UUID,
    ) -> ApiResponse:
        self.require_permission(context, "system.ip_management.view")

        documents = self.ip_ownership_service.list_asset_documents(
            asset_id,
            organisation_id=context.organisation_id,
        )

        return ApiResponse(
            data={"items": documents},
            request_id=context.request_id,
        )

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

    def _audit(self, context, *, action: str, target_type: str, target_id: UUID | None = None) -> None:
        self.core_service.audit_service.record(AuditEvent.create(
            action=action,
            organisation_id=context.organisation_id,
            identity_id=context.identity_id,
            target_type=target_type,
            target_id=target_id,
            request_id=context.request_id,
        ))

    def legal_create_requirement(
        self,
        context,
        *,
        requirement_code: str,
        name: str,
        document_id: UUID,
        document_version_id: UUID,
        action_type: str,
        scope: str,
        enforcement: str = "NOTICE_ONLY",
        description: str | None = None,
        jurisdiction: str | None = None,
        required: bool = True,
        effective_from: str | None = None,
        due_at: str | None = None,
    ) -> ApiResponse:
        """Create a draft legal requirement through Core."""
        requirement = self.legal_compliance_service.create_requirement(
            requirement_code=requirement_code,
            name=name,
            document_id=document_id,
            document_version_id=document_version_id,
            action_type=action_type,
            scope=scope,
            enforcement=enforcement,
            description=description,
            jurisdiction=jurisdiction,
            required=required,
            effective_from=effective_from,
            due_at=due_at,
        )
        return ApiResponse(data=requirement, request_id=context.request_id)

    def legal_activate_requirement(
        self,
        context,
        requirement_id: UUID,
    ) -> ApiResponse:
        requirement = self.legal_compliance_service.activate_requirement(
            requirement_id
        )
        self._audit(
            context,
            action="LEGAL_REQUIREMENT_PUBLISHED",
            target_type="LEGAL_REQUIREMENT",
            target_id=requirement_id,
        )
        return ApiResponse(data=requirement, request_id=context.request_id)

    def legal_retire_requirement(
        self,
        context,
        requirement_id: UUID,
    ) -> ApiResponse:
        requirement = self.legal_compliance_service.retire_requirement(
            requirement_id
        )
        self._audit(
            context,
            action="LEGAL_REQUIREMENT_SUPERSEDED",
            target_type="LEGAL_REQUIREMENT",
            target_id=requirement_id,
        )
        return ApiResponse(data=requirement, request_id=context.request_id)

    def legal_assign_requirement(
        self,
        context,
        requirement_id: UUID,
        *,
        organisation_id: UUID,
        identity_id: UUID | None = None,
        due_at: str | None = None,
    ) -> ApiResponse:
        if organisation_id != context.organisation_id:
            raise AuthorizationError(
                "Legal assignment organisation does not match the current organisation."
            )

        assignment = self.legal_compliance_service.assign_requirement(
            requirement_id,
            organisation_id=organisation_id,
            identity_id=identity_id,
            due_at=due_at,
        )

        self._audit(
            context,
            action="LEGAL_REQUIREMENT_ASSIGNED",
            target_type="LEGAL_REQUIREMENT_ASSIGNMENT",
            target_id=UUID(assignment["id"]),
        )

        return ApiResponse(data=assignment, request_id=context.request_id)

    def legal_required_actions(
        self,
        context,
        *,
        identity_id: UUID | None = None,
    ) -> ApiResponse:
        if identity_id is not None and identity_id != context.identity_id:
            raise AuthorizationError(
                "Legal actions may only be resolved for the current identity."
            )

        actions = self.legal_compliance_service.get_required_actions(
            organisation_id=context.organisation_id,
            identity_id=identity_id or context.identity_id,
        )

        return ApiResponse(
            data={"items": actions},
            request_id=context.request_id,
        )

    def legal_complete_action(
        self,
        context,
        assignment_id: UUID,
        *,
        action_type: str,
        document_version_id: UUID,
        document_checksum: str,
        confirmation_reference: str | None = None,
        signature_provider: str | None = None,
        signature_reference: str | None = None,
        technical_evidence: str | None = None,
    ) -> ApiResponse:
        self._audit(
            context,
            action="LEGAL_ACTION_STARTED",
            target_type="LEGAL_REQUIREMENT_ASSIGNMENT",
            target_id=assignment_id,
        )

        evidence = self.legal_compliance_service.complete_action(
            assignment_id,
            organisation_id=context.organisation_id,
            identity_id=context.identity_id,
            action_type=action_type,
            document_version_id=document_version_id,
            document_checksum=document_checksum,
            confirmation_reference=confirmation_reference,
            signature_provider=signature_provider,
            signature_reference=signature_reference,
            technical_evidence=technical_evidence,
        )

        self._audit(
            context,
            action="LEGAL_ACTION_COMPLETED",
            target_type="LEGAL_ACCEPTANCE_EVIDENCE",
            target_id=UUID(evidence["id"]),
        )

        return ApiResponse(data=evidence, request_id=context.request_id)

    def legal_decline_action(
        self,
        context,
        assignment_id: UUID,
    ) -> ApiResponse:
        assignment = self.legal_compliance_service.decline_action(
            assignment_id,
            organisation_id=context.organisation_id,
            identity_id=context.identity_id,
        )

        self._audit(
            context,
            action="LEGAL_ACTION_DECLINED",
            target_type="LEGAL_REQUIREMENT_ASSIGNMENT",
            target_id=assignment_id,
        )

        return ApiResponse(data=assignment, request_id=context.request_id)


