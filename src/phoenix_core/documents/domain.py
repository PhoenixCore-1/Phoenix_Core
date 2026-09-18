from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID


class DocumentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


@dataclass(frozen=True)
class DocumentContext:
    """
    Generic business context for a document.

    Core deliberately does not know which business module owns the
    referenced context. The module supplies context_type/context_id.
    """

    context_type: str
    context_id: UUID


@dataclass(frozen=True)
class Document:
    id: UUID
    organisation_id: UUID
    name: str
    description: str | None
    mime_type: str
    size_bytes: int
    storage_key: str
    checksum: str | None
    context: DocumentContext | None
    status: DocumentStatus
    created_by_identity_id: UUID
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DocumentVersion:
    id: UUID
    document_id: UUID
    version_number: int
    storage_key: str
    mime_type: str
    size_bytes: int
    checksum: str | None
    created_by_identity_id: UUID
    created_at: datetime


@dataclass(frozen=True)
class DocumentAttachment:
    id: UUID
    organisation_id: UUID
    document_id: UUID
    context: DocumentContext
    attached_by_identity_id: UUID
    created_at: datetime
