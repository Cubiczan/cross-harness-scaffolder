"""CockroachDB storage backend descriptor with serializable retry guidance."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


COCKROACH_DDL = """
-- CockroachDB notes:
-- Prefer UUID/string primary keys and retry serializable transactions.
-- Avoid connection-local advisory-lock assumptions.
create index if not exists idx_chs_round_events_session_round
  on cross_harness_round_events(session_id, phase, round_number);
create index if not exists idx_chs_validations_session_item
  on cross_harness_validations(session_id, item, result);
"""


def cockroach_retry_delays(max_attempts: int = 4, base_seconds: float = 0.05) -> tuple[float, ...]:
    return tuple(base_seconds * (2**attempt) for attempt in range(max_attempts))


@dataclass(frozen=True)
class CockroachStore:
    database_url: str

    def connect(self):
        try:
            import psycopg  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency branch.
            raise RuntimeError("Install the cockroach extra to use CockroachStore: psycopg[binary]") from exc
        return psycopg.connect(self.database_url)

    def migration_sql(self) -> str:
        from cross_harness_scaffolder.core import DATABASE_BLUEPRINT_SQL

        return DATABASE_BLUEPRINT_SQL + "\n" + COCKROACH_DDL

    def run_with_retry(self, operation: Callable[[], T], *, max_attempts: int = 4) -> T:
        last_error: Exception | None = None
        for _delay in cockroach_retry_delays(max_attempts=max_attempts):
            try:
                return operation()
            except Exception as exc:  # pragma: no cover - depends on database driver exceptions.
                if "restart transaction" not in str(exc).lower() and "40001" not in str(exc):
                    raise
                last_error = exc
        if last_error is not None:
            raise last_error
        return operation()
