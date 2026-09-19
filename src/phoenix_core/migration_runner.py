"""Central Phoenix Core migration bootstrap."""

from pathlib import Path


def apply_all(db) -> None:
    """Apply each checked-in SQL migration exactly once."""
    migrations_dir = Path(__file__).resolve().parents[2] / "migrations"
    migrations = sorted(migrations_dir.glob("*.sql"), key=lambda path: path.name)

    if not migrations:
        raise RuntimeError("No Phoenix Core migrations were found.")

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration_name TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )

    try:
        for migration in migrations:
            name = migration.name

            already_applied = db.execute(
                "SELECT 1 FROM schema_migrations WHERE migration_name=?",
                (name,),
            ).fetchone()

            if already_applied:
                continue

            db.executescript(
                migration.read_text(encoding="utf-8-sig")
            )

            from datetime import datetime, timezone

            db.execute(
                "INSERT INTO schema_migrations(migration_name, applied_at) "
                "VALUES (?, ?)",
                (name, datetime.now(timezone.utc).isoformat()),
            )

        db.commit()
    except Exception:
        db.rollback()
        raise
