"""SQLite storage backend for local Cross-Harness runs."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from cross_harness_scaffolder.core import DATABASE_BLUEPRINT_SQL

from .base import PayloadRecord, RoundEventRecord, StorageResult


class SQLiteStore:
    """Small local store backed by Python's standard sqlite3 module."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def initialize(self) -> StorageResult:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.executescript(DATABASE_BLUEPRINT_SQL)
        return StorageResult(ok=True, detail=f"initialized sqlite store at {self.path}")

    def put_payload_blob(self, payload: PayloadRecord) -> StorageResult:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                insert or ignore into cross_harness_payload_blobs
                (content_hash, body, token_estimate, created_at)
                values (?, ?, ?, datetime('now'))
                """,
                (payload.content_hash, payload.body, payload.token_estimate),
            )
        return StorageResult(ok=True, detail=f"stored payload {payload.content_hash}")

    def append_round_event(self, event: RoundEventRecord) -> StorageResult:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                insert into cross_harness_round_events
                (event_id, session_id, phase, round_number, route, payload_id,
                 content_hash, payload_echo, status_snapshot, created_at)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    event.event_id,
                    event.session_id,
                    event.phase,
                    event.round_number,
                    event.route,
                    event.payload_id,
                    event.content_hash,
                    event.payload_echo,
                    event.status_snapshot,
                ),
            )
        return StorageResult(ok=True, detail=f"appended event {event.event_id}")
