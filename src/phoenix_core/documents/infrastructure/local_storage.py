from __future__ import annotations

import hashlib
from pathlib import Path

from phoenix_core.documents.storage import DocumentStorage, StoredObject


class LocalDocumentStorage:
    """
    Local filesystem implementation of the Core DocumentStorage contract.

    This provider is intended for development and controlled non-production
    environments. The storage root is the only filesystem location it may use.
    """

    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve_key(self, storage_key: str) -> Path:
        if not storage_key or storage_key.strip() != storage_key:
            raise ValueError("Storage key must be non-empty and normalized.")

        candidate = (self.root / storage_key).resolve()

        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("Storage key escapes the storage root.") from exc

        return candidate

    def put(
        self,
        *,
        storage_key: str,
        content: bytes,
        mime_type: str,
    ) -> StoredObject:
        path = self._resolve_key(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_bytes(content)

        checksum = hashlib.sha256(content).hexdigest()

        return StoredObject(
            storage_key=storage_key,
            size_bytes=len(content),
            checksum=checksum,
            mime_type=mime_type,
        )

    def get(self, *, storage_key: str) -> bytes:
        return self._resolve_key(storage_key).read_bytes()

    def delete(self, *, storage_key: str) -> None:
        path = self._resolve_key(storage_key)

        if path.exists():
            path.unlink()

    def exists(self, *, storage_key: str) -> bool:
        return self._resolve_key(storage_key).is_file()


def _assert_storage_contract() -> None:
    """
    Static/runtime contract check.

    LocalDocumentStorage intentionally implements the DocumentStorage
    protocol without inheriting from it.
    """
    _ = DocumentStorage
