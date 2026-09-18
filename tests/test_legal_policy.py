from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.legal_policy.domain import PolicyScope, PolicyStatus
from phoenix_core.legal_policy.service import LegalPolicyService


def build_database() -> SQLiteDatabase:
    db = SQLiteDatabase(":memory:")

    from pathlib import Path

    for path in sorted(Path("migrations").glob("00*.sql")):
        db.executescript(path.read_text(encoding="utf-8-sig"))

    return db


def create_identity_and_organisation(db: SQLiteDatabase):
    organisation_id = uuid4()
    identity_id = uuid4()

    db.execute(
        """
        INSERT INTO organisations
        (id, code, name, status, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            str(organisation_id),
            f"ORG-{organisation_id.hex[:8]}",
            f"Organisation {organisation_id.hex[:8]}",
            "ACTIVE",
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    db.execute(
        """
        INSERT INTO identities
        (id, identity_type, status, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            str(identity_id),
            "HUMAN",
            "ACTIVE",
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    db.commit()

    return organisation_id, identity_id


def create_document(db: SQLiteDatabase, organisation_id, identity_id):
    document_id = uuid4()
    now = datetime.now(timezone.utc).isoformat()

    db.execute(
        """
        INSERT INTO documents
        (
            id,
            organisation_id,
            name,
            description,
            mime_type,
            size_bytes,
            storage_key,
            checksum,
            status,
            created_by_identity_id,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(document_id),
            str(organisation_id),
            "Terms and Conditions",
            None,
            "application/pdf",
            100,
            f"policy/{document_id}.pdf",
            None,
            "ACTIVE",
            str(identity_id),
            now,
            now,
        ),
    )

    db.commit()
    return document_id


def test_create_policy_starts_as_draft():
    db = build_database()
    organisation_id, _ = create_identity_and_organisation(db)

    service = LegalPolicyService(db)

    policy = service.create_policy(
        organisation_id,
        "TERMS",
        "EULA",
        required_acceptance=True,
        applicable_scope=PolicyScope.PLATFORM,
    )

    assert policy.status == PolicyStatus.DRAFT
    assert policy.required_acceptance is True
    assert policy.applicable_scope == PolicyScope.PLATFORM

    db.close()


def test_add_policy_version_references_existing_document():
    db = build_database()
    organisation_id, identity_id = create_identity_and_organisation(db)
    document_id = create_document(db, organisation_id, identity_id)

    service = LegalPolicyService(db)

    policy = service.create_policy(
        organisation_id,
        "PRIVACY",
        "PRIVACY_POLICY",
        required_acceptance=True,
    )

    version = service.add_policy_version(
        policy.id,
        1,
        "1.0",
        document_id,
        datetime.now(timezone.utc),
        acceptance_required=True,
    )

    assert version.policy_id == policy.id
    assert version.document_id == document_id
    assert version.version_number == 1
    assert version.status == PolicyStatus.DRAFT

    db.close()


def test_activate_policy_version_activates_policy():
    db = build_database()
    organisation_id, identity_id = create_identity_and_organisation(db)
    document_id = create_document(db, organisation_id, identity_id)

    service = LegalPolicyService(db)

    policy = service.create_policy(
        organisation_id,
        "TERMS",
        "TERMS_OF_SERVICE",
        required_acceptance=True,
    )

    version = service.add_policy_version(
        policy.id,
        1,
        "1.0",
        document_id,
        datetime.now(timezone.utc),
        acceptance_required=True,
    )

    service.activate_policy_version(version.id)

    stored_policy = service.get_policy(policy.id)
    stored_version = service.get_policy_version(version.id)

    assert stored_policy is not None
    assert stored_version is not None
    assert stored_policy.status == PolicyStatus.ACTIVE
    assert stored_version.status == PolicyStatus.ACTIVE

    db.close()


def test_record_acceptance_and_check_exact_version():
    db = build_database()
    organisation_id, identity_id = create_identity_and_organisation(db)
    document_id = create_document(db, organisation_id, identity_id)

    service = LegalPolicyService(db)

    policy = service.create_policy(
        organisation_id,
        "TERMS",
        "TERMS_OF_SERVICE",
        required_acceptance=True,
    )

    version_one = service.add_policy_version(
        policy.id,
        1,
        "1.0",
        document_id,
        datetime.now(timezone.utc),
        acceptance_required=True,
    )

    version_two = service.add_policy_version(
        policy.id,
        2,
        "2.0",
        document_id,
        datetime.now(timezone.utc),
        acceptance_required=True,
    )

    service.record_acceptance(
        policy.id,
        version_one.id,
        organisation_id,
        identity_id,
    )

    assert service.has_accepted(
        organisation_id,
        identity_id,
        version_one.id,
    )

    assert not service.has_accepted(
        organisation_id,
        identity_id,
        version_two.id,
    )

    db.close()


def test_duplicate_acceptance_is_rejected():
    db = build_database()
    organisation_id, identity_id = create_identity_and_organisation(db)
    document_id = create_document(db, organisation_id, identity_id)

    service = LegalPolicyService(db)

    policy = service.create_policy(
        organisation_id,
        "AUP",
        "ACCEPTABLE_USE",
        required_acceptance=True,
    )

    version = service.add_policy_version(
        policy.id,
        1,
        "1.0",
        document_id,
        datetime.now(timezone.utc),
        acceptance_required=True,
    )

    service.record_acceptance(
        policy.id,
        version.id,
        organisation_id,
        identity_id,
    )

    with pytest.raises(Exception):
        service.record_acceptance(
            policy.id,
            version.id,
            organisation_id,
            identity_id,
        )

    db.close()


def test_tenant_isolation_for_acceptance():
    db = build_database()
    organisation_one, identity_one = create_identity_and_organisation(db)
    organisation_two, identity_two = create_identity_and_organisation(db)

    document_id = create_document(db, organisation_one, identity_one)

    service = LegalPolicyService(db)

    policy = service.create_policy(
        organisation_one,
        "TERMS",
        "TERMS_OF_SERVICE",
        required_acceptance=True,
    )

    version = service.add_policy_version(
        policy.id,
        1,
        "1.0",
        document_id,
        datetime.now(timezone.utc),
        acceptance_required=True,
    )

    service.record_acceptance(
        policy.id,
        version.id,
        organisation_one,
        identity_one,
    )

    assert service.has_accepted(
        organisation_one,
        identity_one,
        version.id,
    )

    assert not service.has_accepted(
        organisation_two,
        identity_two,
        version.id,
    )

    db.close()


def test_foreign_keys_prevent_unknown_policy_document():
    db = build_database()
    organisation_id, _ = create_identity_and_organisation(db)

    service = LegalPolicyService(db)

    policy = service.create_policy(
        organisation_id,
        "TERMS",
        "TERMS_OF_SERVICE",
        required_acceptance=True,
    )

    with pytest.raises(Exception):
        service.add_policy_version(
            policy.id,
            1,
            "1.0",
            uuid4(),
            datetime.now(timezone.utc),
            acceptance_required=True,
        )

    db.close()
