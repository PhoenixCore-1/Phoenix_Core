from uuid import uuid4

import pytest

from phoenix_core.api.application import CoreApi
from phoenix_core.api.integration.contracts import IntegrationRequest
from phoenix_core.api.integration.service import CoreIntegrationService
from phoenix_core.errors import ValidationError


def make_service(tmp_path):
    from phoenix_core.infrastructure import SQLiteDatabase
    from phoenix_core.services import CoreFoundationService

    db = SQLiteDatabase(str(tmp_path / "integration.db"))
    service = CoreFoundationService(db)
    service.initialise()
    return db, service


def test_integration_requires_request_id(tmp_path):
    db, service = make_service(tmp_path)
    integration = CoreIntegrationService(CoreApi(db, service))

    with pytest.raises(ValidationError, match="request_id is required"):
        integration.handle(
            IntegrationRequest(
                request_id="",
                operation="identity.current",
            )
        )

    db.close()


def test_integration_requires_operation(tmp_path):
    db, service = make_service(tmp_path)
    integration = CoreIntegrationService(CoreApi(db, service))

    with pytest.raises(ValidationError, match="operation is required"):
        integration.handle(
            IntegrationRequest(
                request_id="req-int-002",
                operation="",
            )
        )

    db.close()


def test_integration_rejects_unsupported_operation(tmp_path):
    db, service = make_service(tmp_path)
    integration = CoreIntegrationService(CoreApi(db, service))

    with pytest.raises(ValidationError, match="Unsupported integration operation"):
        integration.handle(
            IntegrationRequest(
                request_id="req-int-003",
                operation="unknown.operation",
            )
        )

    db.close()


def test_identity_current_requires_authenticated_session(tmp_path):
    db, service = make_service(tmp_path)
    integration = CoreIntegrationService(CoreApi(db, service))

    with pytest.raises(ValidationError, match="authenticated session"):
        integration.handle(
            IntegrationRequest(
                request_id="req-int-004",
                operation="identity.current",
                organisation_id=uuid4(),
            )
        )

    db.close()


def test_identity_current_requires_organisation_context(tmp_path):
    db, service = make_service(tmp_path)
    integration = CoreIntegrationService(CoreApi(db, service))

    with pytest.raises(ValidationError, match="organisation context"):
        integration.handle(
            IntegrationRequest(
                request_id="req-int-005",
                operation="identity.current",
                session_id=uuid4(),
            )
        )

    db.close()
