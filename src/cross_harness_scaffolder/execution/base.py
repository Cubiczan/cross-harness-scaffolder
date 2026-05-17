"""Execution backend contracts."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionRequest:
    command: tuple[str, ...]
    cwd: str | None = None
    timeout_seconds: int = 120
    network_policy: str | None = None
    metadata: dict[str, str] | None = None


@dataclass(frozen=True)
class ExecutionResult:
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    backend: str
    sandbox_id: str | None = None
