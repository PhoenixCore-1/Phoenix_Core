from datetime import datetime, timezone
from uuid import uuid4

from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.legal_policy.access import PolicyAccessEvaluator
from phoenix_core.legal_policy.service import LegalPolicyService


def build_database():
    from pathlib import Path

    db = SQLiteDatabase(":memory:")

    for path in sorted(Path("migrations").glob("00*.sql")):
        db.executescript(path.read_text(encoding="utf-8-sig"))

    return db


def create_identity_and_organisation(db):
    organisation_id = uuid4()
    identity_id = uuid4()
    now = datetime.now(timezone.utc).isoformat()

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
            now,
        ),
    )

    db.execute(
        """
        INSERT INTO identities
        (id, identity_type, status, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (str(identity_id), "HUMAN", "ACTIVE", now),
    )

    db.commit()
    return organisation_id, identity_id


def create_document(db, organisation_id, identity_id):
    document_id = uuid4()
    now = datetime.now(timezone.utc).isoformat()

    db.execute(
        """
        INSERT INTO documents
        (
            id, organisation_id, name, description,
            mime_type, size_bytes, storage_key, checksum,
            status, created_by_identity_id, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(document_id),
            str(organisation_id),
            "Policy",
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


def test_no_required_policies_allows_access():
    db = build_database()
    organisation_id, identity_id = create_identity_and_organisation(db)

    service = LegalPolicyService(db)
    evaluator = PolicyAccessEvaluator(service)

    assert evaluator.required_acceptance_complete(
        organisation_id,
        identity_id,
    )

    db.close()


def test_unaccepted_required_policy_blocks_access():
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

    evaluator = PolicyAccessEvaluator(service)

    assert not evaluator.required_acceptance_complete(
        organisation_id,
        identity_id,
    )

    db.close()


def test_accepted_required_policy_allows_access():
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

    service.record_acceptance(
        policy.id,
        version.id,
        organisation_id,
        identity_id,
    )

    evaluator = PolicyAccessEvaluator(service)

    assert evaluator.required_acceptance_complete(
        organisation_id,
        identity_id,
    )

    db.close()


def test_new_policy_version_requires_new_acceptance():
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

    service.activate_policy_version(version_one.id)

    service.record_acceptance(
        policy.id,
        version_one.id,
        organisation_id,
        identity_id,
    )

    version_two = service.add_policy_version(
        policy.id,
        2,
        "2.0",
        document_id,
        datetime.now(timezone.utc),
        acceptance_required=True,
    )

    service.activate_policy_version(version_two.id)

    evaluator = PolicyAccessEvaluator(service)

    assert not evaluator.required_acceptance_complete(
        organisation_id,
        identity_id,
    )

    db.close()


def test_acceptance_from_another_organisation_does_not_grant_access():
    db = build_database()

    organisation_one, identity_one = create_identity_and_organisation(db)
    organisation_two, identity_two = create_identity_and_organisation(db)

    document_one = create_document(db, organisation_one, identity_one)
    document_two = create_document(db, organisation_two, identity_two)

    service = LegalPolicyService(db)

    policy_one = service.create_policy(
        organisation_one,
        "TERMS",
        "TERMS_OF_SERVICE",
        required_acceptance=True,
    )

    version_one = service.add_policy_version(
        policy_one.id,
        1,
        "1.0",
        document_one,
        datetime.now(timezone.utc),
        acceptance_required=True,
    )

    service.activate_policy_version(version_one.id)

    service.record_acceptance(
        policy_one.id,
        version_one.id,
        organisation_one,
        identity_one,
    )

    policy_two = service.create_policy(
        organisation_two,
        "TERMS",
        "TERMS_OF_SERVICE",
        required_acceptance=True,
    )

    version_two = service.add_policy_version(
        policy_two.id,
        1,
        "1.0",
        document_two,
        datetime.now(timezone.utc),
        acceptance_required=True,
    )

    service.activate_policy_version(version_two.id)

    evaluator = PolicyAccessEvaluator(service)

    assert evaluator.required_acceptance_complete(
        organisation_one,
        identity_one,
    )

    assert not evaluator.required_acceptance_complete(
        organisation_two,
        identity_two,
    )

    db.close()
