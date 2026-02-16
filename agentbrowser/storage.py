"""SQLite storage for profiles, sessions, and recordings."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class Storage:
    """SQLite-backed storage for agentbrowser data."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._init_tables()
        return self._conn

    def _init_tables(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS profiles (
                name TEXT PRIMARY KEY,
                cookies TEXT DEFAULT '[]',
                local_storage TEXT DEFAULT '{}',
                session_storage TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS recordings (
                name TEXT PRIMARY KEY,
                actions TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                description TEXT DEFAULT ''
            );
        """)
        self.conn.commit()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # --- Profiles ---

    def save_profile(
        self,
        name: str,
        cookies: list[dict[str, Any]],
        local_storage: dict[str, str] | None = None,
        session_storage: dict[str, str] | None = None,
    ) -> None:
        """Save or update a browser profile."""
        now = self._now()
        self.conn.execute(
            """INSERT INTO profiles (name, cookies, local_storage, session_storage, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET
                 cookies=excluded.cookies,
                 local_storage=excluded.local_storage,
                 session_storage=excluded.session_storage,
                 updated_at=excluded.updated_at""",
            (
                name,
                json.dumps(cookies),
                json.dumps(local_storage or {}),
                json.dumps(session_storage or {}),
                now,
                now,
            ),
        )
        self.conn.commit()

    def load_profile(self, name: str) -> dict[str, Any] | None:
        """Load a profile by name. Returns None if not found."""
        row = self.conn.execute(
            "SELECT * FROM profiles WHERE name = ?", (name,)
        ).fetchone()
        if row is None:
            return None
        return {
            "name": row["name"],
            "cookies": json.loads(row["cookies"]),
            "local_storage": json.loads(row["local_storage"]),
            "session_storage": json.loads(row["session_storage"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_profiles(self) -> list[dict[str, str]]:
        """List all profiles."""
        rows = self.conn.execute(
            "SELECT name, created_at, updated_at FROM profiles ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_profile(self, name: str) -> bool:
        """Delete a profile. Returns True if it existed."""
        cur = self.conn.execute("DELETE FROM profiles WHERE name = ?", (name,))
        self.conn.commit()
        return cur.rowcount > 0

    # --- Recordings ---

    def save_recording(
        self, name: str, actions: list[dict[str, Any]], description: str = ""
    ) -> None:
        """Save a recorded action sequence."""
        now = self._now()
        self.conn.execute(
            """INSERT INTO recordings (name, actions, created_at, description)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET
                 actions=excluded.actions,
                 description=excluded.description""",
            (name, json.dumps(actions), now, description),
        )
        self.conn.commit()

    def load_recording(self, name: str) -> list[dict[str, Any]] | None:
        """Load a recording by name."""
        row = self.conn.execute(
            "SELECT actions FROM recordings WHERE name = ?", (name,)
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["actions"])

    def list_recordings(self) -> list[dict[str, str]]:
        """List all recordings."""
        rows = self.conn.execute(
            "SELECT name, created_at, description FROM recordings ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_recording(self, name: str) -> bool:
        """Delete a recording."""
        cur = self.conn.execute("DELETE FROM recordings WHERE name = ?", (name,))
        self.conn.commit()
        return cur.rowcount > 0

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
