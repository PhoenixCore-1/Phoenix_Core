from pathlib import Path


def test_integration_service_remains_framework_independent():
    source = Path(
        "src/phoenix_core/api/integration/service.py"
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


def test_integration_contracts_remain_framework_independent():
    source = Path(
        "src/phoenix_core/api/integration/contracts.py"
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


def test_integration_service_does_not_create_database_authority():
    source = Path(
        "src/phoenix_core/api/integration/service.py"
    ).read_text(encoding="utf-8")

    forbidden_patterns = (
        "sqlite3",
        "SQLiteDatabase",
        "connect(",
        ".execute(",
        ".executescript(",
    )

    for pattern in forbidden_patterns:
        assert pattern not in source
