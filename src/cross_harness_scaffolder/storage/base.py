"""Database storage contracts and URL parsing."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from urllib.parse import parse_qs, urlparse


class StorageCapability(str, Enum):
    SQLITE_LOCAL = "sqlite_local"
    POSTGRES_SHARED = "postgres_shared"
    COCKROACH_DISTRIBUTED = "cockroach_distributed"


@dataclass(frozen=True)
class DatabaseConfig:
    scheme: str
    database_url: str
    capability: StorageCapability
    driver_hint: str
    requires_external_dependency: bool
    query: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class PayloadRecord:
    content_hash: str
    body: str
    token_estimate: int


@dataclass(frozen=True)
class RoundEventRecord:
    event_id: str
    session_id: str
    phase: int
    round_number: int
    route: str
    payload_id: str
    content_hash: str
    payload_echo: str
    status_snapshot: str


@dataclass(frozen=True)
class StorageResult:
    ok: bool
    detail: str


def build_database_config(database_url: str) -> DatabaseConfig:
    parsed = urlparse(database_url)
    scheme = parsed.scheme.lower()
    query = {key: tuple(values) for key, values in parse_qs(parsed.query).items()}

    if scheme in ("sqlite", "sqlite3"):
        return DatabaseConfig(
            scheme=scheme,
            database_url=database_url,
            capability=StorageCapability.SQLITE_LOCAL,
            driver_hint="sqlite3",
            requires_external_dependency=False,
            query=query,
        )
    if scheme in ("postgres", "postgresql"):
        return DatabaseConfig(
            scheme=scheme,
            database_url=database_url,
            capability=StorageCapability.POSTGRES_SHARED,
            driver_hint="psycopg",
            requires_external_dependency=True,
            query=query,
        )
    if scheme in ("cockroach", "cockroachdb"):
        return DatabaseConfig(
            scheme=scheme,
            database_url=database_url,
            capability=StorageCapability.COCKROACH_DISTRIBUTED,
            driver_hint="psycopg with serializable retry",
            requires_external_dependency=True,
            query=query,
        )
    raise ValueError(f"unsupported database URL scheme: {scheme or 'missing'}")
