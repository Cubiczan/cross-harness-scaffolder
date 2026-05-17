"""Contracts for live harness adapters."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from cross_harness_scaffolder.core import HarnessProfile


@dataclass(frozen=True)
class HarnessAdapterResult:
    ok: bool
    detail: str
    artifact_path: str | None = None


class HarnessAdapter(Protocol):
    profile: HarnessProfile

    def send_packet(self, packet: str, *, session_id: str) -> HarnessAdapterResult:
        ...

    def receive_response(self, *, session_id: str) -> str | None:
        ...
