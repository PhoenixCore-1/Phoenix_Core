from pathlib import Path


def test_core_api_has_no_direct_sql():
    source = Path(
        "src/phoenix_core/api/application.py"
    ).read_text(encoding="utf-8")

    assert ".execute(" not in source
    assert ".executescript(" not in source
    assert "sqlite3" not in source
    assert "SELECT " not in source.upper()
    assert "INSERT " not in source.upper()
    assert "UPDATE " not in source.upper()
    assert "DELETE " not in source.upper()


def test_core_api_does_not_expose_password_hash():
    source = Path(
        "src/phoenix_core/api/application.py"
    ).read_text(encoding="utf-8")

    assert "password_hash" not in source


def test_core_api_uses_request_context_resolver():
    source = Path(
        "src/phoenix_core/api/application.py"
    ).read_text(encoding="utf-8")

    assert "RequestContextResolver" in source
    assert "resolve_context" in source


def test_core_api_remains_framework_independent():
    source = Path(
        "src/phoenix_core/api/application.py"
    ).read_text(encoding="utf-8")

    forbidden_frameworks = (
        "fastapi",
        "flask",
        "django",
        "starlette",
    )

    lowered = source.lower()

    for framework in forbidden_frameworks:
        assert framework not in lowered
