"""Command-backed live harness adapters with explicit permission boundaries."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from cross_harness_scaffolder.core import HarnessProfile, ascii_only, get_harness_profile

from .base import HarnessAdapterResult


@dataclass(frozen=True)
class NativeAdapterSpec:
    name: str
    profile_name: str
    adapter_type: str
    permission_boundary: str
    stable_surface: str


class CommandHarnessAdapter:
    """Run a local harness command with the packet on stdin.

    The adapter never invokes a shell. The caller must provide the command tuple
    explicitly so permissions remain visible at the call site.
    """

    def __init__(
        self,
        profile: HarnessProfile,
        command: tuple[str, ...],
        *,
        cwd: str | Path | None = None,
        timeout_seconds: int = 300,
        max_output_bytes: int = 65536,
        dry_run: bool = False,
    ) -> None:
        if not command:
            raise ValueError("command must include an executable")
        self.profile = profile
        self.command = tuple(command)
        self.cwd = Path(cwd) if cwd else None
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes
        self.dry_run = dry_run
        self._responses: dict[str, str] = {}

    def send_packet(self, packet: str, *, session_id: str) -> HarnessAdapterResult:
        if self.dry_run:
            return HarnessAdapterResult(ok=True, detail=f"dry run for {self.profile.system}: {' '.join(self.command)}")
        try:
            completed = subprocess.run(
                self.command,
                input=ascii_only(packet),
                text=True,
                capture_output=True,
                cwd=self.cwd,
                timeout=self.timeout_seconds,
                shell=False,
                check=False,
            )
        except FileNotFoundError as exc:
            return HarnessAdapterResult(ok=False, detail=f"command not found: {exc.filename}")
        except subprocess.TimeoutExpired:
            return HarnessAdapterResult(ok=False, detail=f"command timed out after {self.timeout_seconds}s")

        response = completed.stdout[-self.max_output_bytes :]
        self._responses[session_id] = response
        detail = f"{self.profile.system} command exited {completed.returncode}"
        if completed.stderr:
            detail = f"{detail}; stderr captured"
        return HarnessAdapterResult(ok=completed.returncode == 0, detail=detail)

    def receive_response(self, *, session_id: str) -> str | None:
        return self._responses.get(session_id)


def build_command_adapter(
    profile_name: str,
    command: tuple[str, ...],
    **kwargs,
) -> CommandHarnessAdapter:
    return CommandHarnessAdapter(get_harness_profile(profile_name), command, **kwargs)


def native_adapter_specs() -> tuple[NativeAdapterSpec, ...]:
    return (
        NativeAdapterSpec(
            name="file-handoff",
            profile_name="any",
            adapter_type="filesystem",
            permission_boundary="writes inbox_packet.md and reads outbox_response.md only",
            stable_surface="plain files",
        ),
        NativeAdapterSpec(
            name="codex-cli",
            profile_name="codex",
            adapter_type="command",
            permission_boundary="explicit local command tuple, stdin packet, captured stdout",
            stable_surface="local CLI process",
        ),
        NativeAdapterSpec(
            name="claude-code-cli",
            profile_name="claude_code",
            adapter_type="command",
            permission_boundary="explicit local command tuple, stdin packet, captured stdout",
            stable_surface="local CLI process",
        ),
        NativeAdapterSpec(
            name="aider-cli",
            profile_name="aider",
            adapter_type="command",
            permission_boundary="explicit local command tuple, stdin packet, captured stdout",
            stable_surface="local CLI process",
        ),
        NativeAdapterSpec(
            name="superserve-execution",
            profile_name="superserve",
            adapter_type="execution-backend",
            permission_boundary="Firecracker-style sandbox client contract with network policy",
            stable_surface="create_sandbox, run_command, destroy_sandbox",
        ),
    )
