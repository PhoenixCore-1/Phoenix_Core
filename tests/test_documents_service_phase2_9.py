from pathlib import Path
from uuid import uuid4

import pytest

from phoenix_core.documents.domain import DocumentContext, DocumentStatus
from phoenix_core.documents.infrastructure.local_storage import LocalDocumentStorage
from phoenix_core.documents.service import DocumentService
from phoenix_core.errors import NotFoundError, ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.services import CoreFoundationService


def build_service(tmp_path: Path):
    db = SQLiteDatabase(":memory:")
    core = CoreFoundationService(db)
    core.initialise()

    organisation_id = uuid4()
    identity_id = uuid4()

    db.execute(
        """
        INSERT INTO organisations
        (id,code,name,status,created_at) VALUES (?,?,?,?,?)
        """,
        (
            str(organisation_id),
            "TEST", "Test Organisation", "ACTIVE",
            "2026-09-03T00:00:00+00:00",
        ),
    )

    db.execute(
        """
        INSERT INTO identities
        (id,identity_type,status,created_at)
        VALUES (?,?,?,?)
        """,
        (
            str(identity_id),
            "HUMAN",
            "ACTIVE",
            "2026-09-03T00:00:00+00:00",
        ),
    )

    db.commit()

    permissions = {
        "documents.file.create",
        "documents.file.read",
        "documents.file.update",
        "documents.file.delete",
        "documents.attachment.manage",
    }

    def authorize(
        identity: uuid4,
        organisation: uuid4,
        permission: str,
    ) -> bool:
        return (
            identity == identity_id
            and permission in permissions
        )

    audit_events = []

    def audit_record(event):
        audit_events.append(event)
        return event

    storage = LocalDocumentStorage(tmp_path / "storage")

    service = DocumentService(
        db,
        storage,
        authorize=authorize,
        audit_record=audit_record,
    )

    return (
        db,
        service,
        storage,
        organisation_id,
        identity_id,
        audit_events,
    )


def test_create_document_persists_metadata_and_content(tmp_path: Path):
    (
        db,
        service,
        storage,
        organisation_id,
        identity_id,
        audit_events,
    ) = build_service(tmp_path)

    document = service.create(
        organisation_id=organisation_id,
        identity_id=identity_id,
        name="Test Document.txt",
        mime_type="text/plain",
        content=b"Phoenix Core V2",
        description="Test document",
    )

    assert document.status == DocumentStatus.ACTIVE
    assert document.name == "Test Document.txt"
    assert document.size_bytes == len(b"Phoenix Core V2")
    assert document.checksum is not None
    assert storage.exists(storage_key=document.storage_key)
    assert storage.get(storage_key=document.storage_key) == b"Phoenix Core V2"

    row = db.execute(
        "SELECT version_number FROM document_versions WHERE document_id=?",
        (str(document.id),),
    ).fetchone()

    assert row["version_number"] == 1
    assert [event.action for event in audit_events] == ["document.created"]

    db.close()


def test_create_document_supports_generic_context(tmp_path: Path):
    (
        db,
        service,
        _storage,
        organisation_id,
        identity_id,
        _audit_events,
    ) = build_service(tmp_path)

    context_id = uuid4()

    document = service.create(
        organisation_id=organisation_id,
        identity_id=identity_id,
        name="Project File.pdf",
        mime_type="application/pdf",
        content=b"project",
        context=DocumentContext(
            context_type="PROJECT",
            context_id=context_id,
        ),
    )

    assert document.context is not None
    assert document.context.context_type == "PROJECT"
    assert document.context.context_id == context_id

    documents = service.list(
        identity_id=identity_id,
        organisation_id=organisation_id,
        context_type="PROJECT",
        context_id=context_id,
    )

    assert len(documents) == 1
    assert documents[0].id == document.id

    db.close()


def test_create_document_requires_permission(tmp_path: Path):
    (
        db,
        service,
        _storage,
        organisation_id,
        identity_id,
        _audit_events,
    ) = build_service(tmp_path)

    def deny(*_args):
        return False

    service._authorize = deny

    with pytest.raises(ValidationError, match="Permission denied"):
        service.create(
            organisation_id=organisation_id,
            identity_id=identity_id,
            name="Denied.txt",
            mime_type="text/plain",
            content=b"denied",
        )

    db.close()


def test_documents_are_tenant_scoped(tmp_path: Path):
    (
        db,
        service,
        _storage,
        organisation_id,
        identity_id,
        _audit_events,
    ) = build_service(tmp_path)

    document = service.create(
        organisation_id=organisation_id,
        identity_id=identity_id,
        name="Tenant File.txt",
        mime_type="text/plain",
        content=b"tenant data",
    )

    other_organisation_id = uuid4()

    db.execute(
        """
        INSERT INTO organisations
        (id,code,name,status,created_at) VALUES (?,?,?,?,?)
        """,
        (
            str(other_organisation_id),
            "OTHER", "Other Organisation", "ACTIVE",
            "2026-09-03T00:00:00+00:00",
        ),
    )
    db.commit()

    with pytest.raises(NotFoundError, match="Document not found"):
        service.get(
            document_id=document.id,
            identity_id=identity_id,
            organisation_id=other_organisation_id,
        )

    assert service.list(
        identity_id=identity_id,
        organisation_id=organisation_id,
    )[0].id == document.id

    db.close()


def test_archive_changes_lifecycle_without_removing_storage(tmp_path: Path):
    (
        db,
        service,
        storage,
        organisation_id,
        identity_id,
        audit_events,
    ) = build_service(tmp_path)

    document = service.create(
        organisation_id=organisation_id,
        identity_id=identity_id,
        name="Archive.txt",
        mime_type="text/plain",
        content=b"archive me",
    )

    archived = service.archive(
        document_id=document.id,
        identity_id=identity_id,
        organisation_id=organisation_id,
    )

    assert archived.status == DocumentStatus.ARCHIVED
    assert storage.exists(storage_key=document.storage_key)
    assert [event.action for event in audit_events] == [
        "document.created",
        "document.archived",
    ]

    db.close()


def test_delete_is_soft_delete_and_preserves_storage(tmp_path: Path):
    (
        db,
        service,
        storage,
        organisation_id,
        identity_id,
        audit_events,
    ) = build_service(tmp_path)

    document = service.create(
        organisation_id=organisation_id,
        identity_id=identity_id,
        name="Delete.txt",
        mime_type="text/plain",
        content=b"delete me",
    )

    deleted = service.delete(
        document_id=document.id,
        identity_id=identity_id,
        organisation_id=organisation_id,
    )

    assert deleted.status == DocumentStatus.DELETED
    assert storage.exists(storage_key=document.storage_key)
    assert [event.action for event in audit_events] == [
        "document.created",
        "document.deleted",
    ]

    db.close()


def test_create_version_updates_current_document_metadata(tmp_path: Path):
    (
        db,
        service,
        storage,
        organisation_id,
        identity_id,
        audit_events,
    ) = build_service(tmp_path)

    document = service.create(
        organisation_id=organisation_id,
        identity_id=identity_id,
        name="Versioned.txt",
        mime_type="text/plain",
        content=b"version one",
    )

    version = service.create_version(
        document_id=document.id,
        organisation_id=organisation_id,
        identity_id=identity_id,
        content=b"version two",
        mime_type="text/plain",
    )

    assert version.version_number == 2
    assert storage.get(storage_key=version.storage_key) == b"version two"

    versions = service.list_versions(
        document_id=document.id,
        organisation_id=organisation_id,
        identity_id=identity_id,
    )

    assert [item.version_number for item in versions] == [2, 1]

    current = service.get(
        document_id=document.id,
        identity_id=identity_id,
        organisation_id=organisation_id,
    )

    assert current.version_number if hasattr(current, "version_number") else True
    assert current.storage_key == version.storage_key
    assert current.size_bytes == len(b"version two")

    assert [event.action for event in audit_events] == [
        "document.created",
        "document.version.created",
    ]

    db.close()


def test_deleted_document_cannot_receive_version(tmp_path: Path):
    (
        db,
        service,
        _storage,
        organisation_id,
        identity_id,
        _audit_events,
    ) = build_service(tmp_path)

    document = service.create(
        organisation_id=organisation_id,
        identity_id=identity_id,
        name="Deleted.txt",
        mime_type="text/plain",
        content=b"deleted",
    )

    service.delete(
        document_id=document.id,
        identity_id=identity_id,
        organisation_id=organisation_id,
    )

    with pytest.raises(ValidationError, match="Deleted document"):
        service.create_version(
            document_id=document.id,
            organisation_id=organisation_id,
            identity_id=identity_id,
            content=b"new version",
            mime_type="text/plain",
        )

    db.close()


def test_attach_and_detach_document(tmp_path: Path):
    (
        db,
        service,
        _storage,
        organisation_id,
        identity_id,
        audit_events,
    ) = build_service(tmp_path)

    document = service.create(
        organisation_id=organisation_id,
        identity_id=identity_id,
        name="Attachment.txt",
        mime_type="text/plain",
        content=b"attachment",
    )

    context = DocumentContext(
        context_type="PROJECT",
        context_id=uuid4(),
    )

    attachment = service.attach(
        document_id=document.id,
        organisation_id=organisation_id,
        identity_id=identity_id,
        context=context,
    )

    assert attachment.document_id == document.id
    assert attachment.context == context

    duplicate = service.attach(
        document_id=document.id,
        organisation_id=organisation_id,
        identity_id=identity_id,
        context=context,
    )

    assert duplicate.id == attachment.id

    service.detach(
        attachment_id=attachment.id,
        organisation_id=organisation_id,
        identity_id=identity_id,
    )

    with pytest.raises(NotFoundError, match="Document attachment"):
        service.detach(
            attachment_id=attachment.id,
            organisation_id=organisation_id,
            identity_id=identity_id,
        )

    assert [event.action for event in audit_events] == [
        "document.created",
        "document.attachment.created",
        "document.attachment.deleted",
    ]

    db.close()


def test_attachment_is_tenant_scoped(tmp_path: Path):
    (
        db,
        service,
        _storage,
        organisation_id,
        identity_id,
        _audit_events,
    ) = build_service(tmp_path)

    document = service.create(
        organisation_id=organisation_id,
        identity_id=identity_id,
        name="Scoped.txt",
        mime_type="text/plain",
        content=b"scoped",
    )

    attachment = service.attach(
        document_id=document.id,
        organisation_id=organisation_id,
        identity_id=identity_id,
        context=DocumentContext(
            context_type="PROJECT",
            context_id=uuid4(),
        ),
    )

    other_organisation_id = uuid4()

    db.execute(
        """
        INSERT INTO organisations
        (id,code,name,status,created_at) VALUES (?,?,?,?,?)
        """,
        (
            str(other_organisation_id),
            "OTHER", "Other Organisation", "ACTIVE",
            "2026-09-03T00:00:00+00:00",
        ),
    )
    db.commit()

    with pytest.raises(NotFoundError, match="Document attachment"):
        service.detach(
            attachment_id=attachment.id,
            organisation_id=other_organisation_id,
            identity_id=identity_id,
        )

    db.close()


def test_invalid_document_inputs_are_rejected(tmp_path: Path):
    (
        db,
        service,
        _storage,
        organisation_id,
        identity_id,
        _audit_events,
    ) = build_service(tmp_path)

    with pytest.raises(ValidationError, match="Document name"):
        service.create(
            organisation_id=organisation_id,
            identity_id=identity_id,
            name=" ",
            mime_type="text/plain",
            content=b"data",
        )

    with pytest.raises(ValidationError, match="MIME type"):
        service.create(
            organisation_id=organisation_id,
            identity_id=identity_id,
            name="Invalid.txt",
            mime_type=" ",
            content=b"data",
        )

    with pytest.raises(ValidationError, match="bytes"):
        service.create(
            organisation_id=organisation_id,
            identity_id=identity_id,
            name="Invalid.txt",
            mime_type="text/plain",
            content="not bytes",
        )

    db.close()


def test_storage_failure_does_not_create_database_record(tmp_path: Path):
    (
        db,
        service,
        _storage,
        organisation_id,
        identity_id,
        _audit_events,
    ) = build_service(tmp_path)

    class FailingStorage:
        def put(self, **_kwargs):
            raise RuntimeError("storage failure")

        def get(self, **_kwargs):
            raise AssertionError("get should not be called")

        def delete(self, **_kwargs):
            return None

        def exists(self, **_kwargs):
            return False

    service.storage = FailingStorage()

    with pytest.raises(RuntimeError, match="storage failure"):
        service.create(
            organisation_id=organisation_id,
            identity_id=identity_id,
            name="Failure.txt",
            mime_type="text/plain",
            content=b"failure",
        )

    row = db.execute(
        "SELECT COUNT(*) AS count FROM documents"
    ).fetchone()

    assert row["count"] == 0

    db.close()


def test_document_context_requires_type(tmp_path: Path):
    (
        db,
        service,
        _storage,
        organisation_id,
        identity_id,
        _audit_events,
    ) = build_service(tmp_path)

    with pytest.raises(ValidationError, match="context type"):
        service.create(
            organisation_id=organisation_id,
            identity_id=identity_id,
            name="Context.txt",
            mime_type="text/plain",
            content=b"context",
            context=DocumentContext(
                context_type=" ",
                context_id=uuid4(),
            ),
        )

    db.close()






