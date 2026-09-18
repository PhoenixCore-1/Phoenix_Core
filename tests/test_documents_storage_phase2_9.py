from pathlib import Path

import pytest

from phoenix_core.documents.infrastructure.local_storage import LocalDocumentStorage


def test_put_get_and_exists(tmp_path: Path):
    storage = LocalDocumentStorage(tmp_path)

    result = storage.put(
        storage_key="documents/test/example.txt",
        content=b"Phoenix Core V2",
        mime_type="text/plain",
    )

    assert result.storage_key == "documents/test/example.txt"
    assert result.size_bytes == len(b"Phoenix Core V2")
    assert result.checksum == (
        "f2877ef30eeaf78c1b8e80cd3f31e0029d534ef673b85e9d1c37df2dd6a608cc"
    )
    assert result.mime_type == "text/plain"

    assert storage.exists(storage_key="documents/test/example.txt")
    assert storage.get(storage_key="documents/test/example.txt") == b"Phoenix Core V2"


def test_delete_removes_object(tmp_path: Path):
    storage = LocalDocumentStorage(tmp_path)

    storage.put(
        storage_key="documents/test/delete.txt",
        content=b"delete me",
        mime_type="text/plain",
    )

    assert storage.exists(storage_key="documents/test/delete.txt")

    storage.delete(storage_key="documents/test/delete.txt")

    assert not storage.exists(storage_key="documents/test/delete.txt")


def test_nested_storage_keys_are_supported(tmp_path: Path):
    storage = LocalDocumentStorage(tmp_path)

    storage.put(
        storage_key="tenant/documents/2026/example.pdf",
        content=b"PDF content",
        mime_type="application/pdf",
    )

    assert storage.get(
        storage_key="tenant/documents/2026/example.pdf"
    ) == b"PDF content"


@pytest.mark.parametrize(
    "storage_key",
    [
        "../outside.txt",
        "../../outside.txt",
        "/absolute/path.txt",
        "tenant/../../outside.txt",
        " tenant/file.txt",
        "tenant/file.txt ",
        "",
    ],
)
def test_storage_key_cannot_escape_or_use_invalid_format(
    tmp_path: Path,
    storage_key: str,
):
    storage = LocalDocumentStorage(tmp_path)

    with pytest.raises(ValueError):
        storage.put(
            storage_key=storage_key,
            content=b"blocked",
            mime_type="text/plain",
        )


def test_checksum_is_sha256(tmp_path: Path):
    storage = LocalDocumentStorage(tmp_path)

    result = storage.put(
        storage_key="documents/checksum.txt",
        content=b"Phoenix",
        mime_type="text/plain",
    )

    assert result.checksum is not None
    assert len(result.checksum) == 64
