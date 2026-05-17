"""PostgreSQL storage backend descriptor.

The package keeps psycopg optional so the core scaffold remains dependency-free.
Install with `pip install cross-harness-scaffolder[postgres]` before opening a
real connection.
"""
from __future__ import annotations

from dataclasses import dataclass


POSTGRES_DDL = """
-- PostgreSQL notes:
-- Use the core schema plus JSONB-capable application columns where needed.
-- Recommended indexes:
create index if not exists idx_chs_round_events_session_round
  on cross_harness_round_events(session_id, phase, round_number);
create index if not exists idx_chs_items_session_status
  on cross_harness_items(session_id, status, third_party_status);
create index if not exists idx_chs_participants_session
  on cross_harness_participants(session_id, role);
"""


@dataclass(frozen=True)
class PostgresStore:
    database_url: str

    def connect(self):
        try:
            import psycopg  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency branch.
            raise RuntimeError("Install the postgres extra to use PostgresStore: psycopg[binary]") from exc
        return psycopg.connect(self.database_url)

    def migration_sql(self) -> str:
        from cross_harness_scaffolder.core import DATABASE_BLUEPRINT_SQL

        return DATABASE_BLUEPRINT_SQL + "\n" + POSTGRES_DDL
