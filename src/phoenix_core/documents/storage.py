from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StoredObject:
    storage_key: str
    size_bytes: int
    checksum: str | None
    mime_type: str


class DocumentStorage(Protocol):
    """
    Storage contract for Phoenix Core documents.

    Implementations may use local filesystem storage, object storage,
    cloud storage, or another provider without changing Core domain
    or business-module contracts.
    """

    def put(
        self,
        *,
        storage_key: str,
        content: bytes,
        mime_type: str,
    ) -> StoredObject:
        ...

    def get(self, *, storage_key: str) -> bytes:
        ...

    def delete(self, *, storage_key: str) -> None:
        ...

    def exists(self, *, storage_key: str) -> bool:
        ...
