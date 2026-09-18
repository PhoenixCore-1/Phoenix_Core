from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "phoenix_core"

def test_no_local_database_files_are_tracked_in_source():
    assert not list(ROOT.glob("*.db"))
    assert not list(ROOT.glob("*.sqlite"))
    assert not list(ROOT.glob("*.sqlite3"))

def test_core_package_exists():
    assert (SRC / "__init__.py").exists()

def test_domain_packages_exist():
    for package in [
        "identity", "users", "organisations", "roles", "permissions",
        "auth", "sessions", "modules", "licensing", "audit", "security"
    ]:
        assert (SRC / package / "__init__.py").exists()
