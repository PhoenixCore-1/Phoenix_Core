"""Minimal SQLite infrastructure for the first V2 vertical slice."""

import sqlite3
from pathlib import Path


MIGRATIONS = [
    "001_core_foundation.sql",
    "002_core_configuration.sql",
    "003_core_communications.sql",
    "004_core_documents.sql",
    "005_core_jobs.sql",
    "006_core_legal_policy_acceptance.sql",
]


class SQLiteDatabase:
    def __init__(self, path: str | Path):
        self.path = str(path)

        # FastAPI's TestClient executes request handling in a worker thread.
        # Core owns a single SQLite connection for this lightweight V2
        # infrastructure, so allow that connection to be used across the
        # request boundary. Production deployments can move to a pooled
        # connection strategy without changing the Core API contract.
        self.connection = sqlite3.connect(
            self.path,
            check_same_thread=False,
        )
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def initialise_schema(self):
        migrations_path = (
            Path(__file__).resolve().parents[2] / "migrations"
        )

        for migration_name in MIGRATIONS:
            migration_path = migrations_path / migration_name
            schema = migration_path.read_text(encoding="utf-8")
            self.connection.executescript(schema)

        self.connection.commit()

    def close(self):
        self.connection.close()

    def execute(self, sql, params=()):
        return self.connection.execute(sql, params)

    def executescript(self, sql):
        return self.connection.executescript(sql)

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def integrity_check(self) -> bool:
        row = self.connection.execute("PRAGMA integrity_check").fetchone()
        return row[0] == "ok"
