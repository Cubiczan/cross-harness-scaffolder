"""Filesystem adapter for manual or semi-automated harness handoffs."""
from __future__ import annotations

from pathlib import Path

from cross_harness_scaffolder.core import HarnessProfile, ascii_only

from .base import HarnessAdapterResult


class FileHarnessAdapter:
    def __init__(self, profile: HarnessProfile, root: str | Path) -> None:
        self.profile = profile
        self.root = Path(root)

    def _session_dir(self, session_id: str) -> Path:
        safe_session = "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in session_id)
        safe_system = "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in self.profile.system.lower())
        return self.root / safe_session / safe_system

    def send_packet(self, packet: str, *, session_id: str) -> HarnessAdapterResult:
        target_dir = self._session_dir(session_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "inbox_packet.md"
        target.write_text(ascii_only(packet), encoding="ascii")
        return HarnessAdapterResult(ok=True, detail=f"wrote packet for {self.profile.system}", artifact_path=str(target))

    def receive_response(self, *, session_id: str) -> str | None:
        response = self._session_dir(session_id) / "outbox_response.md"
        if not response.exists():
            return None
        return response.read_text(encoding="ascii")
