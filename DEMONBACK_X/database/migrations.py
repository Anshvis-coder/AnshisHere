"""Simple forward-only migration runner for DEMONBACK X.

The schema file uses CREATE TABLE IF NOT EXISTS, so fresh installs need no
migrations.  This runner records a `schema_version` in the settings table and
applies any numbered ALTER steps for upgrades from older builds.
"""
from __future__ import annotations

import sqlite3

from database import db

CURRENT_VERSION = 1

MIGRATIONS: dict[int, list[str]] = {
    # 2: [ "ALTER TABLE habits ADD COLUMN example TEXT DEFAULT ''" ],
}


def run_migrations(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT value FROM settings WHERE key='schema_version'").fetchone()
    version = int(row["value"]) if row else 0
    if version == 0:
        # First init (fresh or pre-existing unversioned db): stamp current.
        conn.execute("INSERT INTO settings(key,value) VALUES('schema_version',?) "
                     "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                     (str(CURRENT_VERSION),))
        conn.commit()
        return
    while version < CURRENT_VERSION:
        version += 1
        try:
            with db.transaction() as tconn:
                for stmt in MIGRATIONS.get(version, []):
                    tconn.execute(stmt)
                tconn.execute("UPDATE settings SET value=? WHERE key='schema_version'",
                              (str(version),))
        except sqlite3.Error as e:
            raise RuntimeError(f"Migration {version} failed: {e}") from e
    conn.execute("UPDATE settings SET value=? WHERE key='schema_version'",
                 (str(CURRENT_VERSION),))
    conn.commit()
