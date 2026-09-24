from pathlib import Path

from phoenix_core.http_api.app import create_development_app


def test_production_module_is_registered_on_app_startup(tmp_path: Path):
    app = create_development_app(str(tmp_path / "production.db"))

    row = app.state.db.execute(
        "SELECT code, name, version, status "
        "FROM modules WHERE code=?",
        ("production",),
    ).fetchone()

    assert row is not None
    assert row["code"] == "production"
    assert row["name"] == "Production"
    assert row["version"] == "1.3.25"
    assert row["status"] == "REGISTERED"


def test_production_foundation_is_present(tmp_path: Path):
    app = create_development_app(str(tmp_path / "production.db"))

    tables = {
        row["name"]
        for row in app.state.db.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name LIKE 'production_%'"
        ).fetchall()
    }

    expected = {
        "production_products",
        "production_boms",
        "production_bom_versions",
        "production_bom_components",
        "production_spc_definitions",
        "production_spc_cost_components",
        "production_orders",
        "production_stages",
        "production_quantity_ledger",
        "production_events",
        "production_holds",
    }

    assert expected.issubset(tables)


def test_production_permissions_are_seeded(tmp_path: Path):
    app = create_development_app(str(tmp_path / "production.db"))

    count = app.state.db.execute(
        "SELECT COUNT(*) AS count "
        "FROM permissions WHERE code LIKE 'production.%'"
    ).fetchone()["count"]

    assert count == 15
