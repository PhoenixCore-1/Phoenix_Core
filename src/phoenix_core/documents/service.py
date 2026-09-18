from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from phoenix_core.audit.domain import AuditEvent
from phoenix_core.documents.domain import (
    Document,
    DocumentAttachment,
    DocumentContext,
    DocumentStatus,
    DocumentVersion,
)
from phoenix_core.documents.storage import DocumentStorage
from phoenix_core.errors import NotFoundError, ValidationError
from phoenix_core.infrastructure import SQLiteDatabase


class DocumentService:
    """Owns Core document metadata, lifecycle and storage coordination."""

    def __init__(
        self,
        db: SQLiteDatabase,
        storage: DocumentStorage,
        *,
        authorize=None,
        audit_record=None,
    ):
        self.db = db
        self.storage = storage
        self._authorize = authorize
        self._audit_record = audit_record

    def _require_permission(
        self,
        identity_id: UUID,
        organisation_id: UUID,
        permission: str,
    ) -> None:
        if self._authorize is not None and not self._authorize(
            identity_id,
            organisation_id,
            permission,
        ):
            raise ValidationError("Permission denied.")

    def _require_identity(self, identity_id: UUID) -> None:
        row = self.db.execute(
            "SELECT id FROM identities WHERE id=?",
            (str(identity_id),),
        ).fetchone()

        if not row:
            raise NotFoundError("Identity not found.")

    def _require_active_organisation(self, organisation_id: UUID) -> None:
        row = self.db.execute(
            """
            SELECT id
            FROM organisations
            WHERE id=? AND status='ACTIVE'
            """,
            (str(organisation_id),),
        ).fetchone()

        if not row:
            raise ValidationError("Organisation is not active.")

    @staticmethod
    def _validate_context(context: DocumentContext | None) -> None:
        if context is None:
            return

        if not context.context_type.strip():
            raise ValidationError("Document context type cannot be empty.")

    @staticmethod
    def _validate_document_inputs(
        *,
        name: str,
        mime_type: str,
        content: bytes,
    ) -> None:
        if not name.strip():
            raise ValidationError("Document name cannot be empty.")

        if not mime_type.strip():
            raise ValidationError("Document MIME type cannot be empty.")

        if not isinstance(content, bytes):
            raise ValidationError("Document content must be bytes.")

    def _audit(
        self,
        *,
        action: str,
        organisation_id: UUID,
        identity_id: UUID,
        target_id: UUID,
        target_type: str = "DOCUMENT",
    ) -> None:
        if self._audit_record is None:
            return

        self._audit_record(
            AuditEvent(
                id=uuid4(),
                organisation_id=organisation_id,
                identity_id=identity_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                request_id=None,
                created_at=datetime.now(timezone.utc),
            )
        )

    def create(
        self,
        *,
        organisation_id: UUID,
        identity_id: UUID,
        name: str,
        mime_type: str,
        content: bytes,
        description: str | None = None,
        context: DocumentContext | None = None,
    ) -> Document:
        self._require_identity(identity_id)
        self._require_active_organisation(organisation_id)
        self._require_permission(
            identity_id,
            organisation_id,
            "documents.file.create",
        )
        self._validate_document_inputs(
            name=name,
            mime_type=mime_type,
            content=content,
        )
        self._validate_context(context)

        document_id = uuid4()
        storage_key = (
            f"organisations/{organisation_id}/"
            f"documents/{document_id}/v1"
        )
        now = datetime.now(timezone.utc)

        stored = self.storage.put(
            storage_key=storage_key,
            content=content,
            mime_type=mime_type,
        )

        try:
            self.db.execute(
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
                    context_type,
                    context_id,
                    status,
                    created_by_identity_id,
                    created_at,
                    updated_at
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    str(document_id),
                    str(organisation_id),
                    name,
                    description,
                    stored.mime_type,
                    stored.size_bytes,
                    stored.storage_key,
                    stored.checksum,
                    context.context_type if context else None,
                    str(context.context_id) if context else None,
                    DocumentStatus.ACTIVE.value,
                    str(identity_id),
                    now.isoformat(),
                    now.isoformat(),
                ),
            )

            self.db.execute(
                """
                INSERT INTO document_versions
                (
                    id,
                    document_id,
                    version_number,
                    storage_key,
                    mime_type,
                    size_bytes,
                    checksum,
                    created_by_identity_id,
                    created_at
                )
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    str(uuid4()),
                    str(document_id),
                    1,
                    stored.storage_key,
                    stored.mime_type,
                    stored.size_bytes,
                    stored.checksum,
                    str(identity_id),
                    now.isoformat(),
                ),
            )

            self.db.commit()
        except Exception:
            self.db.rollback()
            self.storage.delete(storage_key=storage_key)
            raise

        self._audit(
            action="document.created",
            organisation_id=organisation_id,
            identity_id=identity_id,
            target_id=document_id,
        )

        return self.get(
            document_id=document_id,
            identity_id=identity_id,
            organisation_id=organisation_id,
        )

    def get(
        self,
        *,
        document_id: UUID,
        identity_id: UUID,
        organisation_id: UUID,
    ) -> Document:
        self._require_identity(identity_id)
        self._require_active_organisation(organisation_id)
        self._require_permission(
            identity_id,
            organisation_id,
            "documents.file.read",
        )

        row = self.db.execute(
            """
            SELECT
                id,
                organisation_id,
                name,
                description,
                mime_type,
                size_bytes,
                storage_key,
                checksum,
                context_type,
                context_id,
                status,
                created_by_identity_id,
                created_at,
                updated_at
            FROM documents
            WHERE id=? AND organisation_id=?
            """,
            (str(document_id), str(organisation_id)),
        ).fetchone()

        if not row:
            raise NotFoundError("Document not found.")

        return self._from_row(row)

    def list(
        self,
        *,
        identity_id: UUID,
        organisation_id: UUID,
        context_type: str | None = None,
        context_id: UUID | None = None,
        status: DocumentStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        self._require_identity(identity_id)
        self._require_active_organisation(organisation_id)
        self._require_permission(
            identity_id,
            organisation_id,
            "documents.file.read",
        )

        if limit < 1 or limit > 500:
            raise ValidationError("Document limit must be between 1 and 500.")

        if offset < 0:
            raise ValidationError("Document offset cannot be negative.")

        clauses = ["organisation_id=?"]
        params: list[str | int] = [str(organisation_id)]

        if context_type is not None:
            clauses.append("context_type=?")
            params.append(context_type)

        if context_id is not None:
            clauses.append("context_id=?")
            params.append(str(context_id))

        if status is not None:
            clauses.append("status=?")
            params.append(status.value)

        rows = self.db.execute(
            f"""
            SELECT
                id,
                organisation_id,
                name,
                description,
                mime_type,
                size_bytes,
                storage_key,
                checksum,
                context_type,
                context_id,
                status,
                created_by_identity_id,
                created_at,
                updated_at
            FROM documents
            WHERE {' AND '.join(clauses)}
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        ).fetchall()

        return [self._from_row(row) for row in rows]

    def archive(
        self,
        *,
        document_id: UUID,
        identity_id: UUID,
        organisation_id: UUID,
    ) -> Document:
        document = self.get(
            document_id=document_id,
            identity_id=identity_id,
            organisation_id=organisation_id,
        )

        self._require_permission(
            identity_id,
            organisation_id,
            "documents.file.update",
        )

        if document.status == DocumentStatus.DELETED:
            raise ValidationError("Deleted document cannot be archived.")

        if document.status == DocumentStatus.ARCHIVED:
            return document

        now = datetime.now(timezone.utc)

        self.db.execute(
            """
            UPDATE documents
            SET status=?, updated_at=?
            WHERE id=? AND organisation_id=?
            """,
            (
                DocumentStatus.ARCHIVED.value,
                now.isoformat(),
                str(document_id),
                str(organisation_id),
            ),
        )
        self.db.commit()

        self._audit(
            action="document.archived",
            organisation_id=organisation_id,
            identity_id=identity_id,
            target_id=document_id,
        )

        return self.get(
            document_id=document_id,
            identity_id=identity_id,
            organisation_id=organisation_id,
        )

    def delete(
        self,
        *,
        document_id: UUID,
        identity_id: UUID,
        organisation_id: UUID,
    ) -> Document:
        document = self.get(
            document_id=document_id,
            identity_id=identity_id,
            organisation_id=organisation_id,
        )

        self._require_permission(
            identity_id,
            organisation_id,
            "documents.file.delete",
        )

        if document.status == DocumentStatus.DELETED:
            return document

        now = datetime.now(timezone.utc)

        self.db.execute(
            """
            UPDATE documents
            SET status=?, updated_at=?
            WHERE id=? AND organisation_id=?
            """,
            (
                DocumentStatus.DELETED.value,
                now.isoformat(),
                str(document_id),
                str(organisation_id),
            ),
        )
        self.db.commit()

        self._audit(
            action="document.deleted",
            organisation_id=organisation_id,
            identity_id=identity_id,
            target_id=document_id,
        )

        return self.get(
            document_id=document_id,
            identity_id=identity_id,
            organisation_id=organisation_id,
        )

    def create_version(
        self,
        *,
        document_id: UUID,
        organisation_id: UUID,
        identity_id: UUID,
        content: bytes,
        mime_type: str,
    ) -> DocumentVersion:
        self._require_identity(identity_id)
        self._require_active_organisation(organisation_id)
        self._require_permission(
            identity_id,
            organisation_id,
            "documents.file.update",
        )

        if not isinstance(content, bytes):
            raise ValidationError("Document content must be bytes.")

        if not mime_type.strip():
            raise ValidationError("Document MIME type cannot be empty.")

        document = self.get(
            document_id=document_id,
            identity_id=identity_id,
            organisation_id=organisation_id,
        )

        if document.status == DocumentStatus.DELETED:
            raise ValidationError("Deleted document cannot receive versions.")

        row = self.db.execute(
            """
            SELECT MAX(version_number) AS version_number
            FROM document_versions
            WHERE document_id=?
            """,
            (str(document_id),),
        ).fetchone()

        current_version = row["version_number"] or 0
        version_number = current_version + 1

        storage_key = (
            f"organisations/{organisation_id}/"
            f"documents/{document_id}/v{version_number}"
        )
        now = datetime.now(timezone.utc)

        stored = self.storage.put(
            storage_key=storage_key,
            content=content,
            mime_type=mime_type,
        )

        try:
            self.db.execute(
                """
                INSERT INTO document_versions
                (
                    id,
                    document_id,
                    version_number,
                    storage_key,
                    mime_type,
                    size_bytes,
                    checksum,
                    created_by_identity_id,
                    created_at
                )
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    str(uuid4()),
                    str(document_id),
                    version_number,
                    stored.storage_key,
                    stored.mime_type,
                    stored.size_bytes,
                    stored.checksum,
                    str(identity_id),
                    now.isoformat(),
                ),
            )

            self.db.execute(
                """
                UPDATE documents
                SET
                    mime_type=?,
                    size_bytes=?,
                    storage_key=?,
                    checksum=?,
                    updated_at=?
                WHERE id=? AND organisation_id=?
                """,
                (
                    stored.mime_type,
                    stored.size_bytes,
                    stored.storage_key,
                    stored.checksum,
                    now.isoformat(),
                    str(document_id),
                    str(organisation_id),
                ),
            )

            self.db.commit()
        except Exception:
            self.db.rollback()
            self.storage.delete(storage_key=storage_key)
            raise

        self._audit(
            action="document.version.created",
            organisation_id=organisation_id,
            identity_id=identity_id,
            target_id=document_id,
        )

        return self.get_version(
            document_id=document_id,
            version_number=version_number,
            organisation_id=organisation_id,
            identity_id=identity_id,
        )

    def get_version(
        self,
        *,
        document_id: UUID,
        version_number: int,
        organisation_id: UUID,
        identity_id: UUID,
    ) -> DocumentVersion:
        self._require_identity(identity_id)
        self._require_active_organisation(organisation_id)
        self._require_permission(
            identity_id,
            organisation_id,
            "documents.file.read",
        )

        self._require_document_belongs_to_organisation(
            document_id,
            organisation_id,
        )

        row = self.db.execute(
            """
            SELECT
                id,
                document_id,
                version_number,
                storage_key,
                mime_type,
                size_bytes,
                checksum,
                created_by_identity_id,
                created_at
            FROM document_versions
            WHERE document_id=? AND version_number=?
            """,
            (str(document_id), version_number),
        ).fetchone()

        if not row:
            raise NotFoundError("Document version not found.")

        return self._version_from_row(row)

    def list_versions(
        self,
        *,
        document_id: UUID,
        organisation_id: UUID,
        identity_id: UUID,
    ) -> list[DocumentVersion]:
        self._require_identity(identity_id)
        self._require_active_organisation(organisation_id)
        self._require_permission(
            identity_id,
            organisation_id,
            "documents.file.read",
        )

        self._require_document_belongs_to_organisation(
            document_id,
            organisation_id,
        )

        rows = self.db.execute(
            """
            SELECT
                id,
                document_id,
                version_number,
                storage_key,
                mime_type,
                size_bytes,
                checksum,
                created_by_identity_id,
                created_at
            FROM document_versions
            WHERE document_id=?
            ORDER BY version_number DESC
            """,
            (str(document_id),),
        ).fetchall()

        return [self._version_from_row(row) for row in rows]

    def attach(
        self,
        *,
        document_id: UUID,
        organisation_id: UUID,
        identity_id: UUID,
        context: DocumentContext,
    ) -> DocumentAttachment:
        self._require_identity(identity_id)
        self._require_active_organisation(organisation_id)
        self._require_permission(
            identity_id,
            organisation_id,
            "documents.attachment.manage",
        )
        self._validate_context(context)

        document = self.get(
            document_id=document_id,
            identity_id=identity_id,
            organisation_id=organisation_id,
        )

        if document.status == DocumentStatus.DELETED:
            raise ValidationError("Deleted document cannot be attached.")

        existing = self.db.execute(
            """
            SELECT
                id,
                organisation_id,
                document_id,
                context_type,
                context_id,
                attached_by_identity_id,
                created_at
            FROM document_attachments
            WHERE organisation_id=?
              AND document_id=?
              AND context_type=?
              AND context_id=?
            """,
            (
                str(organisation_id),
                str(document_id),
                context.context_type,
                str(context.context_id),
            ),
        ).fetchone()

        if existing:
            return self._attachment_from_row(existing)

        attachment_id = uuid4()
        now = datetime.now(timezone.utc)

        self.db.execute(
            """
            INSERT INTO document_attachments
            (
                id,
                organisation_id,
                document_id,
                context_type,
                context_id,
                attached_by_identity_id,
                created_at
            )
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                str(attachment_id),
                str(organisation_id),
                str(document_id),
                context.context_type,
                str(context.context_id),
                str(identity_id),
                now.isoformat(),
            ),
        )
        self.db.commit()

        self._audit(
            action="document.attachment.created",
            organisation_id=organisation_id,
            identity_id=identity_id,
            target_id=attachment_id,
            target_type="DOCUMENT_ATTACHMENT",
        )

        row = self.db.execute(
            """
            SELECT
                id,
                organisation_id,
                document_id,
                context_type,
                context_id,
                attached_by_identity_id,
                created_at
            FROM document_attachments
            WHERE id=?
            """,
            (str(attachment_id),),
        ).fetchone()

        return self._attachment_from_row(row)

    def detach(
        self,
        *,
        attachment_id: UUID,
        organisation_id: UUID,
        identity_id: UUID,
    ) -> None:
        self._require_identity(identity_id)
        self._require_active_organisation(organisation_id)
        self._require_permission(
            identity_id,
            organisation_id,
            "documents.attachment.manage",
        )

        row = self.db.execute(
            """
            SELECT id
            FROM document_attachments
            WHERE id=? AND organisation_id=?
            """,
            (str(attachment_id), str(organisation_id)),
        ).fetchone()

        if not row:
            raise NotFoundError("Document attachment not found.")

        self.db.execute(
            """
            DELETE FROM document_attachments
            WHERE id=? AND organisation_id=?
            """,
            (str(attachment_id), str(organisation_id)),
        )
        self.db.commit()

        self._audit(
            action="document.attachment.deleted",
            organisation_id=organisation_id,
            identity_id=identity_id,
            target_id=attachment_id,
            target_type="DOCUMENT_ATTACHMENT",
        )

    def _require_document_belongs_to_organisation(
        self,
        document_id: UUID,
        organisation_id: UUID,
    ) -> None:
        row = self.db.execute(
            """
            SELECT id
            FROM documents
            WHERE id=? AND organisation_id=?
            """,
            (str(document_id), str(organisation_id)),
        ).fetchone()

        if not row:
            raise NotFoundError("Document not found.")

    @staticmethod
    def _from_row(row) -> Document:
        context = None

        if row["context_type"] is not None:
            context = DocumentContext(
                context_type=row["context_type"],
                context_id=UUID(row["context_id"]),
            )

        return Document(
            id=UUID(row["id"]),
            organisation_id=UUID(row["organisation_id"]),
            name=row["name"],
            description=row["description"],
            mime_type=row["mime_type"],
            size_bytes=row["size_bytes"],
            storage_key=row["storage_key"],
            checksum=row["checksum"],
            context=context,
            status=DocumentStatus(row["status"]),
            created_by_identity_id=UUID(row["created_by_identity_id"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    @staticmethod
    def _version_from_row(row) -> DocumentVersion:
        return DocumentVersion(
            id=UUID(row["id"]),
            document_id=UUID(row["document_id"]),
            version_number=row["version_number"],
            storage_key=row["storage_key"],
            mime_type=row["mime_type"],
            size_bytes=row["size_bytes"],
            checksum=row["checksum"],
            created_by_identity_id=UUID(row["created_by_identity_id"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @staticmethod
    def _attachment_from_row(row) -> DocumentAttachment:
        return DocumentAttachment(
            id=UUID(row["id"]),
            organisation_id=UUID(row["organisation_id"]),
            document_id=UUID(row["document_id"]),
            context=DocumentContext(
                context_type=row["context_type"],
                context_id=UUID(row["context_id"]),
            ),
            attached_by_identity_id=UUID(row["attached_by_identity_id"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
