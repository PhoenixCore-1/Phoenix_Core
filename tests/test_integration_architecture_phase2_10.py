from pathlib import Path


def test_integration_service_does_not_access_database_directly():
    source = Path(
        "src/phoenix_core/api/integration/service.py"
    ).read_text(encoding="utf-8")

    assert ".execute(" not in source
    assert ".executescript(" not in source
    assert "sqlite3" not in source
    assert "SELECT " not in source.upper()
    assert "INSERT " not in source.upper()
    assert "UPDATE " not in source.upper()
    assert "DELETE " not in source.upper()
