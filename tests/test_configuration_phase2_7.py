import json
from uuid import UUID

import pytest

from phoenix_core.configuration.domain import FeatureFlag, SettingDefinition
from phoenix_core.errors import ConflictError, NotFoundError, ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.services import CoreFoundationService


def make_service(tmp_path):
    db = SQLiteDatabase(tmp_path / "test.db")
    service = CoreFoundationService(db)
    service.initialise()
    return service, db


def make_org(service, code="ACME"):
    return service.create_organisation(code, f"{code} Organisation")


def test_global_typed_settings(tmp_path):
    service, db = make_service(tmp_path)
    try:
        setting = service.create_setting("max_items", 25, "INTEGER")
        assert setting.value_type == "INTEGER"
        assert setting.value == "25"
        assert service.get_setting("max_items").value == "25"
    finally:
        db.close()


def test_setting_value_validation(tmp_path):
    service, db = make_service(tmp_path)
    try:
        with pytest.raises(ValidationError):
            SettingDefinition.create("x", "yes", "BOOLEAN")
        with pytest.raises(ValidationError):
            SettingDefinition.create("x", 1, "UNKNOWN")
    finally:
        db.close()


def test_organisation_setting_isolation(tmp_path):
    service, db = make_service(tmp_path)
    try:
        a = make_org(service, "A")
        b = make_org(service, "B")
        service.create_setting("timezone", "Africa/Johannesburg", organisation_id=a.id)
        with pytest.raises(NotFoundError):
            service.get_setting("timezone", organisation_id=b.id)
    finally:
        db.close()


def test_effective_setting_uses_org_override_then_global(tmp_path):
    service, db = make_service(tmp_path)
    try:
        org = make_org(service)
        service.create_setting("timezone", "UTC")
        assert service.get_effective_setting("timezone", organisation_id=org.id).value == "UTC"
        service.create_setting("timezone", "Africa/Johannesburg", organisation_id=org.id)
        assert service.get_effective_setting("timezone", organisation_id=org.id).value == "Africa/Johannesburg"
    finally:
        db.close()


def test_setting_update_does_not_create_duplicate(tmp_path):
    service, db = make_service(tmp_path)
    try:
        service.create_setting("page_size", 20, "INTEGER")
        service.create_setting("page_size", 50, "INTEGER")
        assert len(service.list_settings()) == 1
        assert service.get_setting("page_size").value == "50"
    finally:
        db.close()


def test_feature_flag_lifecycle_and_default(tmp_path):
    service, db = make_service(tmp_path)
    try:
        org = make_org(service)
        assert service.is_feature_enabled("new_ui", organisation_id=org.id) is False
        flag = service.create_feature_flag("new_ui", True, organisation_id=org.id)
        assert flag.enabled is True
        service.set_feature_flag("new_ui", False, organisation_id=org.id)
        assert service.is_feature_enabled("new_ui", organisation_id=org.id) is False
    finally:
        db.close()


def test_feature_flag_scope_isolation(tmp_path):
    service, db = make_service(tmp_path)
    try:
        a = make_org(service, "A")
        b = make_org(service, "B")
        service.create_feature_flag("beta", True, organisation_id=a.id)
        assert service.is_feature_enabled("beta", organisation_id=a.id) is True
        assert service.is_feature_enabled("beta", organisation_id=b.id) is False
    finally:
        db.close()


def test_duplicate_feature_flag_rejected(tmp_path):
    service, db = make_service(tmp_path)
    try:
        service.create_feature_flag("beta")
        with pytest.raises(ConflictError):
            service.create_feature_flag("beta")
    finally:
        db.close()


def test_org_configuration_requires_active_org(tmp_path):
    service, db = make_service(tmp_path)
    try:
        org = make_org(service)
        service.suspend_organisation(org.id)
        with pytest.raises(ValidationError):
            service.create_setting("x", "y", organisation_id=org.id)
        with pytest.raises(ValidationError):
            service.create_feature_flag("x", organisation_id=org.id)
    finally:
        db.close()


def test_configuration_does_not_replace_permission_or_entitlement(tmp_path):
    service, db = make_service(tmp_path)
    try:
        org = make_org(service)
        service.create_setting("production.enabled", True, "BOOLEAN", organisation_id=org.id)
        service.create_feature_flag("production", True, organisation_id=org.id)
        # Configuration/flag alone do not grant a user capability.
        assert service.is_feature_enabled("production", organisation_id=org.id) is True
    finally:
        db.close()
