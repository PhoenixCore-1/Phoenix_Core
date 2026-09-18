"""Central Phoenix Core migration bootstrap."""

from pathlib import Path


def apply_all(db) -> None:
    """Apply every checked-in SQL migration in deterministic numeric order."""
    migrations_dir = Path(__file__).resolve().parents[2] / "migrations"
    migrations = sorted(migrations_dir.glob("*.sql"), key=lambda path: path.name)
    if not migrations:
        raise RuntimeError("No Phoenix Core migrations were found.")
    try:
        for migration in migrations:
            db.executescript(migration.read_text(encoding="utf-8-sig"))
        db.commit()
    except Exception:
        db.rollback()
        raise
