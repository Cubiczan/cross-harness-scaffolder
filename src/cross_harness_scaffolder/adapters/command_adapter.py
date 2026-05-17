"""Command-backed live harness adapters with explicit permission boundaries."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from cross_harness_scaffolder.core import HarnessProfile, ascii_only, get_harness_profile

from .base import HarnessAdapterResult


class AdapterStability(str, Enum):
    STABLE = "stable"
    GATED = "gated"
    EXPERIMENTAL = "experimental"


@dataclass(frozen=True)
class NativeAdapterSpec:
    name: str
    profile_name: str
    adapter_type: str
    permission_boundary: str
    stable_surface: str
    stability: AdapterStability = AdapterStability.STABLE
    requires_human_approval: bool = True
    notes: str = ""


@dataclass(frozen=True)
class PermissionReview:
    reviewer: str
    command_surface: str
    auth_scope: str
    workspace_scope: str
    audit_sink: str
    approved: bool = False
    risk_notes: str = ""

    def validate(self) -> tuple[str, ...]:
        missing = []
        for field in ("reviewer", "command_surface", "auth_scope", "workspace_scope", "audit_sink"):
            if not getattr(self, field):
                missing.append(field)
        if not self.approved:
            missing.append("approved")
        return tuple(missing)


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
        permission_review: PermissionReview | None = None,
        adapter_spec: NativeAdapterSpec | None = None,
    ) -> None:
        if not command:
            raise ValueError("command must include an executable")
        self.profile = profile
        self.command = tuple(command)
        self.cwd = Path(cwd) if cwd else None
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes
        self.dry_run = dry_run
        self.permission_review = permission_review
        self.adapter_spec = adapter_spec
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


def native_adapter_spec(name: str) -> NativeAdapterSpec:
    normalized = name.strip().lower()
    for spec in native_adapter_specs():
        if spec.name == normalized:
            return spec
    raise KeyError(f"unknown native adapter spec: {name}")


def build_native_adapter(
    spec_name: str,
    command: tuple[str, ...],
    *,
    permission_review: PermissionReview | None = None,
    allow_gated: bool = False,
    **kwargs,
) -> CommandHarnessAdapter:
    spec = native_adapter_spec(spec_name)
    if spec.adapter_type != "command":
        raise ValueError(f"native adapter spec is not command-executable: {spec.name}")
    if spec.stability == AdapterStability.GATED:
        if not allow_gated:
            raise PermissionError(f"{spec.name} is gated; pass allow_gated=True after permission-model review")
        if permission_review is None:
            raise PermissionError(f"{spec.name} requires a PermissionReview")
        missing = permission_review.validate()
        if missing:
            raise PermissionError(f"{spec.name} permission review incomplete: {', '.join(missing)}")
    return CommandHarnessAdapter(
        get_harness_profile(spec.profile_name),
        command,
        permission_review=permission_review,
        adapter_spec=spec,
        **kwargs,
    )


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
        NativeAdapterSpec(
            name="cursor-cli",
            profile_name="cursor",
            adapter_type="command",
            permission_boundary="explicit local command tuple, stdin packet, captured stdout",
            stable_surface="local CLI process",
            stability=AdapterStability.GATED,
            notes="Enable only when the local Cursor command surface is pinned and audit-reviewed.",
        ),
        NativeAdapterSpec(
            name="continue-cli",
            profile_name="continue",
            adapter_type="command",
            permission_boundary="explicit local command tuple, stdin packet, captured stdout",
            stable_surface="local CLI process",
            stability=AdapterStability.GATED,
            notes="Continue supports multiple providers; pin provider, model, workspace, and command flags.",
        ),
        NativeAdapterSpec(
            name="cline-file-handoff",
            profile_name="cline",
            adapter_type="filesystem",
            permission_boundary="manual inbox/outbox files, no automated tool execution",
            stable_surface="plain files",
            stability=AdapterStability.STABLE,
            notes="Use file handoff until IDE extension automation is explicitly permissioned.",
        ),
        NativeAdapterSpec(
            name="roo-code-file-handoff",
            profile_name="roo_code",
            adapter_type="filesystem",
            permission_boundary="manual inbox/outbox files, no automated tool execution",
            stable_surface="plain files",
            stability=AdapterStability.STABLE,
            notes="Use file handoff for mode-specific Roo workflows.",
        ),
        NativeAdapterSpec(
            name="copilot-cli",
            profile_name="github_copilot",
            adapter_type="command",
            permission_boundary="explicit local command tuple, stdin packet, captured stdout",
            stable_surface="local CLI process",
            stability=AdapterStability.GATED,
            notes="Enable only for GitHub-authenticated environments with repository scope reviewed.",
        ),
        NativeAdapterSpec(
            name="sourcegraph-cody-cli",
            profile_name="sourcegraph_cody",
            adapter_type="command",
            permission_boundary="explicit local command tuple, stdin packet, captured stdout",
            stable_surface="local CLI process",
            stability=AdapterStability.GATED,
            notes="Pin endpoint and code graph scope before enabling.",
        ),
        NativeAdapterSpec(
            name="glm-cli",
            profile_name="glm5",
            adapter_type="command",
            permission_boundary="explicit local command tuple, stdin packet, captured stdout",
            stable_surface="local provider CLI process",
            stability=AdapterStability.GATED,
            notes="Treat provider credentials as external to packets.",
        ),
        NativeAdapterSpec(
            name="deepseek-cli",
            profile_name="deepseek",
            adapter_type="command",
            permission_boundary="explicit local command tuple, stdin packet, captured stdout",
            stable_surface="local provider CLI process",
            stability=AdapterStability.GATED,
            notes="Treat provider credentials as external to packets.",
        ),
        NativeAdapterSpec(
            name="qwen-cli",
            profile_name="qwen",
            adapter_type="command",
            permission_boundary="explicit local command tuple, stdin packet, captured stdout",
            stable_surface="local provider CLI process",
            stability=AdapterStability.GATED,
            notes="Treat provider credentials as external to packets.",
        ),
    )


def stable_native_adapter_specs() -> tuple[NativeAdapterSpec, ...]:
    return tuple(spec for spec in native_adapter_specs() if spec.stability == AdapterStability.STABLE)


def gated_native_adapter_specs() -> tuple[NativeAdapterSpec, ...]:
    return tuple(spec for spec in native_adapter_specs() if spec.stability == AdapterStability.GATED)
