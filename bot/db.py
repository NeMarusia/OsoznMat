from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class UserState:
    user_id: int
    current_node: str
    waiting_for: str | None = None


class StateStorage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_states (
                    user_id INTEGER PRIMARY KEY,
                    current_node TEXT NOT NULL,
                    waiting_for TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def get(self, user_id: int) -> UserState | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id, current_node, waiting_for FROM user_states WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return UserState(user_id=row[0], current_node=row[1], waiting_for=row[2])

    def set(self, user_id: int, current_node: str, waiting_for: str | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_states (user_id, current_node, waiting_for)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    current_node = excluded.current_node,
                    waiting_for = excluded.waiting_for,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, current_node, waiting_for),
            )

