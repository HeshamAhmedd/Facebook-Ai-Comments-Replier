from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ReplyRecord:
    comment_id: str
    reply_text: str
    replied_at: int
    post_id: Optional[str] = None


class StateStore:
    def __init__(self, db_path: str | Path = "fb_agent_state.sqlite3") -> None:
        self.db_path = str(db_path)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS replied (
                    comment_id TEXT PRIMARY KEY,
                    reply_text TEXT NOT NULL,
                    replied_at INTEGER NOT NULL,
                    post_id TEXT
                )
                """
            )
            con.commit()

    def has_replied(self, comment_id: str) -> bool:
        with sqlite3.connect(self.db_path) as con:
            row = con.execute(
                "SELECT 1 FROM replied WHERE comment_id = ? LIMIT 1", (comment_id,)
            ).fetchone()
            return row is not None

    def mark_replied(self, comment_id: str, reply_text: str, post_id: str | None) -> None:
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "INSERT OR REPLACE INTO replied(comment_id, reply_text, replied_at, post_id) VALUES (?, ?, ?, ?)",
                (comment_id, reply_text, int(time.time()), post_id),
            )
            con.commit()
