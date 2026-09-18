from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORE_ROOT = PROJECT_ROOT / "src" / "phoenix_core"
FRAMEWORK_ROOT = PROJECT_ROOT / "src" / "phoenix_framework"


def python_files(root: Path):
    return root.rglob("*.py")


def test_framework_exists_as_separate_package():
    assert FRAMEWORK_ROOT.is_dir()
    assert (FRAMEWORK_ROOT / "__init__.py").is_file()


def test_core_does_not_import_framework():
    forbidden = "phoenix_framework"

    for path in python_files(CORE_ROOT):
        text = path.read_text(encoding="utf-8")
        assert forbidden not in text, f"Core imports Framework: {path}"


def test_framework_contracts_do_not_import_core_database_or_infrastructure():
    contracts_root = FRAMEWORK_ROOT / "contracts"

    forbidden = (
        "sqlite3",
        "SQLiteDatabase",
        "phoenix_core.infrastructure",
        "direct_sql",
    )

    for path in python_files(contracts_root):
        text = path.read_text(encoding="utf-8")

        for marker in forbidden:
            assert marker not in text, (
                f"Framework contract contains forbidden infrastructure "
                f"dependency '{marker}': {path}"
            )


def test_framework_contracts_do_not_depend_on_business_modules():
    contracts_root = FRAMEWORK_ROOT / "contracts"

    forbidden = (
        "crm",
        "sales",
        "production",
        "inventory",
        "procurement",
        "accounts",
        "projects",
    )

    for path in python_files(contracts_root):
        text = path.read_text(encoding="utf-8").lower()

        for marker in forbidden:
            assert marker not in text, (
                f"Framework contract contains business-module dependency "
                f"'{marker}': {path}"
            )
