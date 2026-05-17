"""Consensus-hardened Cross-Harness Scaffolder.

Cross-Harness Scaffolder helps engineering teams use multiple AI coding
harnesses as complementary build surfaces. A harness can own local edits,
specification attack, codebase search, refactor execution, frontier reasoning,
or final validation. Consensus Hardening Protocol gates keep the handoff
auditable before implementation work is treated as locked.

Canonical Consensus Hardening Protocol source:
https://codeberg.org/cubiczan/consensus-hardening-protocol
Harness definition reference: https://arize.com/blog/what-is-an-agent-harness/
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import string
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


PROTOCOL_VERSION = "Cross-Harness Scaffolder v0.1.0"
SCAFFOLDER_SHORT_NAME = "CHS"
CANONICAL_PROTOCOL_NAME = "Consensus Hardening Protocol"
CANONICAL_PROTOCOL_URL = "https://codeberg.org/cubiczan/consensus-hardening-protocol"

HARNESS_DEFINITION = (
    "A harness is the closed-loop operating architecture around a model: "
    "tool iteration, context management, skill/tool registry, subagent "
    "management, session persistence, prompt assembly, lifecycle hooks, and "
    "permission controls. Cross-Harness Scaffolder coordinates those harness "
    "layers so each system does the work it is structurally best at."
)

RETIRED_TERMS = ("V" + "CL", "T" + "LP", "L" + "TP", "triang" + "ulat")


class Phase(int, Enum):
    FOUNDATION = 0
    SPEC = 1
    IMPLEMENTATION = 2


class Status(str, Enum):
    EXPLORING = "EXPLORING"
    PROVISIONAL = "PROVISIONAL"
    PROVISIONAL_LOCK = "PROVISIONAL_LOCK"
    LOCKED = "LOCKED"
    CONVERGED = "CONVERGED"
    UNRESOLVED = "UNRESOLVED"
    REFRAME_REQUIRED = "REFRAME_REQUIRED"
    HALT = "HALT"
    PHASE_GATE_FAIL = "PHASE_GATE_FAIL"


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    HALT = "HALT"
    REFRAME = "REFRAME"
    ITERATE = "ITERATE"
    CONVERGED = "CONVERGED"
    PHASE_GATE_FAIL = "PHASE_GATE_FAIL"


class ModelDelta(str, Enum):
    NONE = "NONE"
    MINOR = "MINOR"
    SIGNIFICANT = "SIGNIFICANT"


class ModelTier(int, Enum):
    SMALL = 1
    MID = 2
    HIGH = 3
    FRONTIER = 4
    UNKNOWN = 99


class CrossHarnessLayer(str, Enum):
    REPO_STATE = "repo_state"
    TASK_FLOW = "task_flow"
    SYSTEM_DESIGN = "system_design"
    SECURITY_BOUNDARY = "security_boundary"
    BUSINESS_RULE = "business_rule"
    DEPLOYMENT_CONTEXT = "deployment_context"


@dataclass(frozen=True)
class HarnessProfile:
    system: str
    model: str
    role: str
    strengths: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    default_tools: tuple[str, ...] = ()
    best_for: tuple[str, ...] = ()

    def render(self) -> str:
        return "\n".join(
            [
                f"- System: {self.system}",
                f"  Model: {self.model}",
                f"  Role: {self.role}",
                f"  Strengths: {list(self.strengths) or 'UNKNOWN'}",
                f"  Constraints: {list(self.constraints) or 'UNKNOWN'}",
                f"  Tools: {list(self.default_tools) or 'UNKNOWN'}",
                f"  Best For: {list(self.best_for) or 'UNKNOWN'}",
            ]
        )


@dataclass(frozen=True)
class ContextCheck:
    memory_tools: str = "UNAVAILABLE"
    prior_scaffold_runs: int = 0
    prior_lock_versions: tuple[str, ...] = ()
    legacy_warning: bool = False
    related_locks: tuple[str, ...] = ()
    assessment: str = "SPARSE"
    action: str = "PROCEED"

    def render(self) -> str:
        return "\n".join(
            [
                "CONTEXT_CHECK:",
                f"- Memory/Tools: {self.memory_tools}",
                f"- Prior Cross-Harness Runs: {self.prior_scaffold_runs} found",
                f"- Prior Lock Versions: {list(self.prior_lock_versions) or 'NONE'}",
                f"- Legacy Warning: {'YES' if self.legacy_warning else 'NO'}",
                f"- Related Locks: {list(self.related_locks) or 'NONE'}",
                f"- Assessment: {self.assessment}",
                f"- Action: {self.action}",
            ]
        )


@dataclass(frozen=True)
class ModelParityCheck:
    origin: str
    partner: str
    delta: ModelDelta
    advisory: str = ""

    @property
    def can_proceed(self) -> bool:
        return self.delta != ModelDelta.SIGNIFICANT

    def render(self) -> str:
        lines = [
            "MODEL_PARITY_CHECK:",
            f"- Origin: {self.origin}",
            f"- Partner: {self.partner}",
            f"- Delta: {self.delta.value}",
        ]
        if self.advisory:
            lines.append(f"- Advisory: {self.advisory}")
        return "\n".join(lines)


@dataclass(frozen=True)
class R0Gate:
    solvable: tuple[str, str]
    scoped: tuple[str, str]
    valid: tuple[str, str]
    worth_it: tuple[str, str]

    @property
    def status(self) -> str:
        return "HALT" if any(item[0] == "FATAL" for item in self._items()) else "PROCEED"

    def _items(self) -> tuple[tuple[str, str], ...]:
        return (self.solvable, self.scoped, self.valid, self.worth_it)

    def render(self) -> str:
        return "\n".join(
            [
                "R0_GATE:",
                f"- Solvable: {self.solvable[0]} - {self.solvable[1]}",
                f"- Scoped: {self.scoped[0]} - {self.scoped[1]}",
                f"- Valid: {self.valid[0]} - {self.valid[1]}",
                f"- Worth_it: {self.worth_it[0]} - {self.worth_it[1]}",
                f"GATE_STATUS: {self.status}",
            ]
        )


@dataclass(frozen=True)
class FoundationDisclosure:
    weakest_assumptions: tuple[str, ...]
    invalidation_conditions: tuple[str, ...]
    key_vulnerability: str

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not 1 <= len(self.weakest_assumptions) <= 3:
            errors.append("weakest_assumptions must include 1-3 items")
        if not 1 <= len(self.invalidation_conditions) <= 2:
            errors.append("invalidation_conditions must include 1-2 items")
        if not self.key_vulnerability:
            errors.append("key_vulnerability is required")
        return errors

    def render(self) -> str:
        lines = ["FOUNDATION_DISCLOSURE:", "", "WEAKEST_ASSUMPTIONS:"]
        lines.extend(f"{idx}. {item}" for idx, item in enumerate(self.weakest_assumptions, 1))
        lines.extend(["", "WHAT_COULD_INVALIDATE:"])
        lines.extend(f"{idx}. {item}" for idx, item in enumerate(self.invalidation_conditions, 1))
        lines.extend(["", "KEY_VULNERABILITY:", f"- IF attacking this: {self.key_vulnerability}"])
        return "\n".join(lines)


@dataclass(frozen=True)
class FoundationAttack:
    assumption_attacks: tuple[str, ...]
    invalidation_exploitation: tuple[str, ...]
    vulnerability_strike: str
    foundation_score: int
    attack_summary: str

    def verdict(self) -> Verdict:
        return Verdict.PASS if self.foundation_score >= 70 else Verdict.REFRAME


@dataclass(frozen=True)
class CrossHarnessDiagnosis:
    item: str
    observed_layer: CrossHarnessLayer
    constraint_layer: CrossHarnessLayer
    diagnosis: str

    def render(self) -> str:
        return (
            f"- {self.item}: observed={self.observed_layer.value}; "
            f"constraint={self.constraint_layer.value}; diagnosis={self.diagnosis}"
        )


@dataclass(frozen=True)
class CrossHarnessDossier:
    core_problem: str
    goal_state: tuple[str, ...]
    current_state: tuple[str, ...]
    prior_decisions: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    scope: tuple[str, ...] = ()
    origin_direction: tuple[str, ...] = ()
    prior_round_summary: tuple[str, ...] = ()
    unknowns_carried: tuple[str, ...] = ()
    foundation_score: int | None = None
    structural_vulnerabilities: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.core_problem or self.core_problem == "UNKNOWN":
            errors.append("CORE PROBLEM is required")
        populated = sum(bool(value) for value in (self.goal_state, self.current_state, self.constraints, self.scope))
        if populated < 3:
            errors.append("dossier must include at least three populated context sections")
        return errors

    def render(self) -> str:
        return "\n".join(
            [
                "DOSSIER:",
                f"CORE PROBLEM: {self.core_problem or 'UNKNOWN'}",
                f"GOAL STATE: {list(self.goal_state) or 'UNKNOWN'}",
                f"CURRENT STATE: {list(self.current_state) or 'UNKNOWN'}",
                f"PRIOR DECISIONS: {list(self.prior_decisions) or 'NONE'}",
                f"CONSTRAINTS: {list(self.constraints) or 'UNKNOWN'}",
                f"UNKNOWNS: {list(self.unknowns) or 'NONE'}",
                f"SCOPE: {list(self.scope) or 'UNKNOWN'}",
                f"ORIGIN DIRECTION: {list(self.origin_direction) or 'UNKNOWN'}",
                f"PRIOR_ROUND_SUMMARY: {list(self.prior_round_summary) or 'NONE'}",
                f"UNKNOWNS_CARRIED: {list(self.unknowns_carried) or 'NONE'}",
                f"FOUNDATION_SCORE: {self.foundation_score if self.foundation_score is not None else 'UNKNOWN'}",
                f"STRUCTURAL_VULNERABILITIES: {list(self.structural_vulnerabilities) or 'NONE'}",
            ]
        )


@dataclass(frozen=True)
class PayloadEnvelope:
    body: str
    route: str = "RX"
    payload_id: str = ""

    def __post_init__(self) -> None:
        if not self.payload_id:
            object.__setattr__(self, "payload_id", make_payload_id())

    def render(self) -> str:
        return (
            f"BEGIN_PAYLOAD [{self.route}] [{self.payload_id}]\n"
            f"{ascii_only(self.body)}\n"
            f"END_PAYLOAD [{self.route}] [{self.payload_id}]"
        )

    @property
    def echo(self) -> str:
        return f"[{self.route}] [{self.payload_id}] CONFIRMED"


@dataclass(frozen=True)
class CrossHarnessSession:
    title: str
    origin: HarnessProfile
    partner: HarnessProfile
    human_bridge: str
    dossier: CrossHarnessDossier
    validators: tuple[HarnessProfile, ...] = ()
    context_check: ContextCheck = ContextCheck()
    parity: ModelParityCheck | None = None
    r0_gate: R0Gate | None = None
    foundation: FoundationDisclosure | None = None
    diagnostics: tuple[CrossHarnessDiagnosis, ...] = ()
    phase: Phase = Phase.FOUNDATION
    round_number: int = 0
    status: Status = Status.EXPLORING
    blind_spots: tuple[str, ...] = ()
    structural_vulnerabilities: tuple[str, ...] = ()

    @property
    def participants(self) -> tuple[HarnessProfile, ...]:
        return (self.origin, self.partner, *self.validators)


@dataclass(frozen=True)
class ScaffoldArtifact:
    path: str
    purpose: str
    content: str

    @property
    def content_hash(self) -> str:
        return content_hash(self.content)

    @property
    def token_estimate(self) -> int:
        return estimate_tokens(self.content)

    def manifest_entry(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "purpose": self.purpose,
            "content_hash": self.content_hash,
            "token_estimate": self.token_estimate,
        }


@dataclass(frozen=True)
class ScaffoldPackage:
    artifacts: tuple[ScaffoldArtifact, ...]

    @property
    def total_token_estimate(self) -> int:
        return sum(artifact.token_estimate for artifact in self.artifacts)

    def manifest(self) -> dict[str, Any]:
        return {
            "artifact_count": len(self.artifacts),
            "total_token_estimate": self.total_token_estimate,
            "artifacts": [artifact.manifest_entry() for artifact in self.artifacts],
        }


@dataclass(frozen=True)
class ConsensusFinding:
    check: str
    status: str
    detail: str
    severity: str = "info"


@dataclass(frozen=True)
class ConsensusHardeningReport:
    verdict: Verdict
    score: int
    findings: tuple[ConsensusFinding, ...]

    @property
    def passed(self) -> bool:
        return self.verdict == Verdict.PASS

    def render_markdown(self) -> str:
        lines = [
            "# Consensus Hardening Review",
            "",
            f"Protocol: {CANONICAL_PROTOCOL_NAME}",
            f"Scaffolder: {PROTOCOL_VERSION}",
            f"Verdict: {self.verdict.value}",
            f"Score: {self.score}",
            "",
            "## Findings",
            "",
        ]
        for finding in self.findings:
            lines.append(f"- {finding.status} | {finding.check} | {finding.severity} | {finding.detail}")
        return "\n".join(lines)


TRIGGER_PHRASES = (
    "cross-harness validation",
    "codex claude code handoff",
    "multi-harness consensus",
    "cross-harness loop",
    "partner harness packet",
    "foundation attack",
    "spec validation",
    "devil's advocate",
    "council spawn",
    "payload markers",
    "consensus hardening",
    "cross-harness",
    "cross-harness diagnostics",
)


HARNESS_ARCHETYPES = {
    "codex": HarnessProfile(
        system="Codex",
        model="GPT-5.5 or configured OpenAI coding model",
        role="implementation_harness",
        strengths=(
            "repo-local execution",
            "tests and build verification",
            "patch discipline",
            "database and migration scaffolding",
        ),
        constraints=("protect user worktree", "sandbox and tool availability vary", "needs explicit approvals for pushes"),
        default_tools=("shell", "apply_patch", "pytest", "git"),
        best_for=("edits", "test repair", "packaging", "local validation"),
    ),
    "claude": HarnessProfile(
        system="Claude",
        model="Claude Opus or configured Anthropic model",
        role="spec_adversary_harness",
        strengths=(
            "long-form architecture critique",
            "assumption attack",
            "requirements synthesis",
            "failure-mode enumeration",
        ),
        constraints=("must not self-certify final locks", "needs payload echo discipline"),
        default_tools=("reasoning", "document critique", "spec review"),
        best_for=("spec attack", "blind spot review", "architecture alternatives"),
    ),
    "claude_code": HarnessProfile(
        system="Claude Code",
        model="Claude Opus or configured Anthropic coding model",
        role="code_review_harness",
        strengths=(
            "codebase navigation",
            "large-context review",
            "architecture refactor planning",
            "implementation critique",
        ),
        constraints=("must preserve repository ownership boundaries", "must respect phase gates"),
        default_tools=("filesystem", "terminal", "git", "code search"),
        best_for=("review", "architecture plan", "second-pass edits"),
    ),
    "cursor": HarnessProfile(
        system="Cursor",
        model="configured Cursor model",
        role="ide_refactor_harness",
        strengths=(
            "interactive IDE refactors",
            "symbol-aware edits",
            "developer-in-the-loop iteration",
            "fast local code navigation",
        ),
        constraints=("context depends on project indexing", "manual approval may be needed for broad refactors"),
        default_tools=("IDE index", "search", "inline edits", "terminal"),
        best_for=("targeted refactors", "developer review", "UI wiring"),
    ),
    "github_copilot": HarnessProfile(
        system="GitHub Copilot",
        model="configured Copilot model",
        role="github_ide_agent_harness",
        strengths=(
            "IDE-native code completion and chat",
            "GitHub issue and pull request workflows",
            "broad IDE coverage",
            "agent mode in supported clients",
        ),
        constraints=("feature set varies by IDE", "repository access follows GitHub permissions"),
        default_tools=("IDE plugin", "GitHub context", "chat", "agent mode"),
        best_for=("inline coding", "GitHub workflow handoff", "PR-oriented validation"),
    ),
    "vscode": HarnessProfile(
        system="VS Code",
        model="configured extension model",
        role="extension_host_harness",
        strengths=(
            "large extension ecosystem",
            "task and debugger integration",
            "terminal-native workflows",
            "host for Copilot, Continue, Cline, Roo Code, and other agents",
        ),
        constraints=("capabilities depend on installed extensions", "workspace trust and extension permissions matter"),
        default_tools=("extensions", "terminal", "debugger", "tasks", "MCP clients"),
        best_for=("extension-based agents", "debug workflows", "frontend iteration"),
    ),
    "visual_studio": HarnessProfile(
        system="Visual Studio",
        model="configured Visual Studio AI model",
        role="enterprise_ide_harness",
        strengths=(
            "large .NET and C++ solution support",
            "debugger and profiler integration",
            "enterprise Windows development",
            "Copilot-assisted IDE workflows",
        ),
        constraints=("best fit for supported Microsoft stacks", "feature availability varies by edition"),
        default_tools=("solution explorer", "debugger", "profiler", "Copilot plugin"),
        best_for=("C#/.NET", "C++", "Windows desktop", "enterprise IDE validation"),
    ),
    "jetbrains_junie": HarnessProfile(
        system="JetBrains Junie",
        model="configured JetBrains AI model",
        role="jetbrains_agent_harness",
        strengths=(
            "JetBrains IDE project intelligence",
            "multi-step autonomous coding",
            "JVM and polyglot refactor support",
            "test and run configuration awareness",
        ),
        constraints=("requires JetBrains AI availability", "project model and indexing must be current"),
        default_tools=("JetBrains IDE index", "run configurations", "tests", "agent planner"),
        best_for=("JVM refactors", "structured IDE tasks", "test-aware implementation"),
    ),
    "antigravity": HarnessProfile(
        system="Antigravity",
        model="configured Antigravity model",
        role="agentic_task_harness",
        strengths=(
            "multi-step task execution",
            "browser-assisted workflows",
            "parallel work planning",
            "implementation follow-through",
        ),
        constraints=("capabilities depend on configured workspace and connectors", "needs scoped tasks"),
        default_tools=("workspace tools", "browser", "terminal", "task planner"),
        best_for=("workflow execution", "integration passes", "end-to-end validation"),
    ),
    "windsurf": HarnessProfile(
        system="Windsurf",
        model="configured Windsurf model",
        role="ai_ide_harness",
        strengths=(
            "AI-first IDE workflows",
            "multi-file agent edits",
            "flow-oriented coding sessions",
            "VS Code setting migration",
        ),
        constraints=("agent behavior depends on workspace context", "validate generated changes externally"),
        default_tools=("IDE index", "Cascade", "terminal", "multi-file edits"),
        best_for=("greenfield scaffolds", "multi-file feature work", "UI iteration"),
    ),
    "zed": HarnessProfile(
        system="Zed",
        model="configured Zed AI provider",
        role="open_source_ai_editor_harness",
        strengths=(
            "fast collaborative editor",
            "agent panel for project edits",
            "external agent integration",
            "low-latency review loops",
        ),
        constraints=("agent capabilities depend on configured providers", "external agent execution needs local setup"),
        default_tools=("agent panel", "assistant threads", "external agents", "terminal"),
        best_for=("fast review", "external-agent coordination", "collaborative edits"),
    ),
    "kiro": HarnessProfile(
        system="Kiro",
        model="configured Kiro model",
        role="spec_driven_agentic_ide_harness",
        strengths=(
            "spec-first development",
            "agent hooks",
            "implementation plans",
            "docs and test generation",
        ),
        constraints=("service availability and quotas may vary", "specs must remain synced with implementation"),
        default_tools=("specs", "agent hooks", "MCP", "implementation planner"),
        best_for=("requirements-to-code", "spec maintenance", "test plan generation"),
    ),
    "replit_agent": HarnessProfile(
        system="Replit Agent",
        model="configured Replit Agent model",
        role="cloud_app_builder_harness",
        strengths=(
            "browser-based app construction",
            "hosted workspace execution",
            "checkpoint rollback",
            "deployment-oriented workflows",
        ),
        constraints=("cloud workspace boundary", "production data must be isolated from agent experiments"),
        default_tools=("Replit workspace", "agent checkpoints", "deployment tools", "database tools"),
        best_for=("prototype apps", "hosted demos", "deployment smoke tests"),
    ),
    "continue": HarnessProfile(
        system="Continue",
        model="configured Continue model",
        role="open_source_ide_assistant_harness",
        strengths=(
            "model-flexible IDE assistance",
            "open-source configuration",
            "VS Code and JetBrains workflows",
            "team-shared assistant templates",
        ),
        constraints=("quality depends on configured model and context providers", "team configs require governance"),
        default_tools=("IDE extension", "CLI", "local or cloud models", "MCP"),
        best_for=("bring-your-own-model teams", "local model workflows", "policy-controlled coding assistance"),
    ),
    "cline": HarnessProfile(
        system="Cline",
        model="configured Cline model",
        role="open_source_agent_extension_harness",
        strengths=(
            "autonomous IDE task execution",
            "file editing with permission gates",
            "terminal and browser use",
            "MCP server creation and use",
        ),
        constraints=("requires explicit approval discipline", "workspace side effects must be reviewed"),
        default_tools=("VS Code extension", "terminal", "browser", "MCP"),
        best_for=("agentic local tasks", "browser validation", "tool-building experiments"),
    ),
    "roo_code": HarnessProfile(
        system="Roo Code",
        model="configured Roo Code model",
        role="multi_mode_agent_extension_harness",
        strengths=(
            "multi-mode VS Code agent workflows",
            "custom modes",
            "terminal execution",
            "MCP integrations",
        ),
        constraints=("mode configuration must be explicit", "auto-approval settings require caution"),
        default_tools=("VS Code extension", "modes", "terminal", "MCP"),
        best_for=("architect/debug/code mode splits", "custom agent policies", "local automation"),
    ),
    "aider": HarnessProfile(
        system="Aider",
        model="configured Aider model",
        role="terminal_pair_programming_harness",
        strengths=(
            "git-aware terminal pair programming",
            "patch-oriented edits",
            "test and lint loops",
            "works with many models",
        ),
        constraints=("terminal workflow requires clean git hygiene", "large architectural context needs curation"),
        default_tools=("terminal", "git", "lint/test commands", "model adapters"),
        best_for=("patch generation", "CLI-driven edits", "test-driven loops"),
    ),
    "sourcegraph_cody": HarnessProfile(
        system="Sourcegraph Cody",
        model="configured Cody model",
        role="code_search_context_harness",
        strengths=(
            "code graph context",
            "large-codebase search",
            "IDE and web workflows",
            "context-aware code explanations",
        ),
        constraints=("best with indexed repositories", "access follows Sourcegraph configuration"),
        default_tools=("code search", "IDE plugin", "web app", "context engine"),
        best_for=("large repo orientation", "API usage review", "context-grounded explanations"),
    ),
    "tabnine": HarnessProfile(
        system="Tabnine",
        model="configured Tabnine model",
        role="privacy_oriented_completion_harness",
        strengths=(
            "enterprise IDE coverage",
            "privacy-focused assistance",
            "code completion",
            "team policy controls",
        ),
        constraints=("agentic depth varies by plan and IDE", "best used as a completion/review surface"),
        default_tools=("IDE plugin", "completion", "chat", "team policy controls"),
        best_for=("enterprise completion", "private code assistance", "policy-governed teams"),
    ),
    "glm5": HarnessProfile(
        system="GLM 5",
        model="GLM-5",
        role="frontier_reasoning_harness",
        strengths=(
            "frontier reasoning",
            "multilingual code and documentation review",
            "low-correlated critique",
            "algorithmic alternatives",
        ),
        constraints=("tool execution depends on wrapper harness", "validate claims against repo evidence"),
        default_tools=("reasoning", "spec critique", "algorithm review"),
        best_for=("independent review", "China-market or multilingual checks", "algorithm critique"),
    ),
    "deepseek": HarnessProfile(
        system="DeepSeek",
        model="DeepSeek-R1 or configured DeepSeek coding model",
        role="frontier_code_reasoning_harness",
        strengths=(
            "code reasoning",
            "math-heavy implementation checks",
            "cost-efficient critique",
            "algorithm and performance review",
        ),
        constraints=("must ground findings in code evidence", "tool execution depends on wrapper harness"),
        default_tools=("reasoning", "code review", "test design"),
        best_for=("performance review", "algorithm checks", "edge-case testing"),
    ),
    "qwen": HarnessProfile(
        system="Qwen",
        model="Qwen3-Coder or configured Qwen model",
        role="frontier_code_generation_harness",
        strengths=(
            "code generation",
            "agentic coding workflows",
            "multilingual implementation review",
            "cost-efficient broad critique",
        ),
        constraints=("tool execution depends on wrapper harness", "validate generated patches with local tests"),
        default_tools=("reasoning", "code generation", "code review", "test design"),
        best_for=("implementation alternatives", "large refactor sketches", "multilingual code review"),
    ),
    "superserve": HarnessProfile(
        system="SuperServe",
        model="Firecracker microVM execution backend",
        role="sandbox_validation_harness",
        strengths=(
            "Firecracker microVM isolation",
            "network-restricted validation",
            "ephemeral execution environments",
            "sandbox IDs for audit records",
        ),
        constraints=("requires configured SuperServe client", "never pass secrets through harness packets"),
        default_tools=("microVM sandbox", "command execution", "network policy", "snapshot metadata"),
        best_for=("untrusted code validation", "fresh-environment tests", "release smoke checks"),
    ),
}

HARNESS_ALIASES = {
    "anthropic": "claude",
    "claude-code": "claude_code",
    "claude code": "claude_code",
    "openai": "codex",
    "gpt": "codex",
    "copilot": "github_copilot",
    "github copilot": "github_copilot",
    "gh copilot": "github_copilot",
    "vs code": "vscode",
    "visual studio code": "vscode",
    "vsc": "vscode",
    "vs": "visual_studio",
    "microsoft visual studio": "visual_studio",
    "cursor ide": "cursor",
    "jetbrains": "jetbrains_junie",
    "junie": "jetbrains_junie",
    "jetbrains ai": "jetbrains_junie",
    "google antigravity": "antigravity",
    "windsurf ai": "windsurf",
    "codeium": "windsurf",
    "zed editor": "zed",
    "aws kiro": "kiro",
    "replit": "replit_agent",
    "replit ai": "replit_agent",
    "continue.dev": "continue",
    "continue dev": "continue",
    "roo": "roo_code",
    "roo-code": "roo_code",
    "roo code": "roo_code",
    "sourcegraph": "sourcegraph_cody",
    "cody": "sourcegraph_cody",
    "sourcegraph amp": "sourcegraph_cody",
    "glm-5": "glm5",
    "glm 5": "glm5",
    "zhipu": "glm5",
    "deepseek r1": "deepseek",
    "deepseek-r1": "deepseek",
    "qwen3": "qwen",
    "qwen-3": "qwen",
    "qwen coder": "qwen",
    "qwen-coder": "qwen",
    "qwen3 coder": "qwen",
    "qwen3-coder": "qwen",
    "tongyi": "qwen",
    "firecracker": "superserve",
    "microvm": "superserve",
    "superserve.ai": "superserve",
}


DATABASE_BLUEPRINT_SQL = """
-- Cross-Harness Scaffolder persistence blueprint.
-- Token-efficient design: session state is normalized; large packet bodies are
-- content-addressed once and referenced by hash from round events.

create table if not exists cross_harness_sessions (
  session_id text primary key,
  protocol_version text not null,
  canonical_protocol text not null,
  title text not null,
  human_bridge text not null,
  phase integer not null default 0,
  round_number integer not null default 0,
  status text not null default 'EXPLORING',
  foundation_score integer,
  created_at text not null,
  updated_at text not null
);

create table if not exists cross_harness_participants (
  participant_id text primary key,
  session_id text not null references cross_harness_sessions(session_id),
  system text not null,
  model text not null,
  role text not null,
  trust_level text not null default 'supervised',
  strengths_json text not null default '[]',
  constraints_json text not null default '[]'
);

create table if not exists cross_harness_items (
  item_id text primary key,
  session_id text not null references cross_harness_sessions(session_id),
  label text not null,
  status text not null,
  agreement integer not null default 0,
  flip_criteria text not null default '',
  diagnostic_observed_layer text not null,
  diagnostic_constraint_layer text not null,
  third_party_status text not null default 'PENDING'
);

create table if not exists cross_harness_payload_blobs (
  content_hash text primary key,
  body text not null,
  token_estimate integer not null,
  created_at text not null
);

create table if not exists cross_harness_round_events (
  event_id text primary key,
  session_id text not null references cross_harness_sessions(session_id),
  phase integer not null,
  round_number integer not null,
  route text not null,
  payload_id text not null,
  content_hash text not null references cross_harness_payload_blobs(content_hash),
  payload_echo text not null,
  status_snapshot text not null,
  created_at text not null
);

create table if not exists cross_harness_validations (
  validation_id text primary key,
  session_id text not null references cross_harness_sessions(session_id),
  validator_system text not null,
  validator_model text not null,
  item text not null,
  challenge text not null,
  result text not null,
  rationale text not null,
  created_at text not null
);
"""


def make_payload_id() -> str:
    return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))


def ascii_only(value: str) -> str:
    return value.encode("ascii", "replace").decode("ascii")


def content_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def estimate_tokens(value: str) -> int:
    return max(1, len(value.split()) + len(value) // 24)


def normalize_harness_key(name: str) -> str:
    key = name.strip().lower().replace("_", " ")
    key = HARNESS_ALIASES.get(key, key)
    return key.replace(" ", "_").replace("-", "_")


def available_harnesses() -> tuple[str, ...]:
    return tuple(sorted(HARNESS_ARCHETYPES))


def get_harness_profile(name: str, *, model: str | None = None, role: str | None = None) -> HarnessProfile:
    key = normalize_harness_key(name)
    if key not in HARNESS_ARCHETYPES:
        raise KeyError(f"unknown harness profile: {name}")
    profile = HARNESS_ARCHETYPES[key]
    if model is None and role is None:
        return profile
    return HarnessProfile(
        system=profile.system,
        model=model or profile.model,
        role=role or profile.role,
        strengths=profile.strengths,
        constraints=profile.constraints,
        default_tools=profile.default_tools,
        best_for=profile.best_for,
    )


def build_harness_council(origin: str, partner: str, *validators: str) -> tuple[HarnessProfile, ...]:
    return tuple(get_harness_profile(name) for name in (origin, partner, *validators))


def validate_payload_envelope(text: str) -> bool:
    match = re.search(
        r"BEGIN_PAYLOAD \[(?P<route>[A-Z]+)\] \[(?P<id>[A-Z0-9]{6})\]\n(?P<body>.*?)\nEND_PAYLOAD \[(?P=route)\] \[(?P=id)\]",
        text,
        re.DOTALL,
    )
    return bool(match)


def extract_payload_marker(text: str) -> str | None:
    match = re.search(r"BEGIN_PAYLOAD \[([A-Z]+)\] \[([A-Z0-9]{6})\]", text)
    if not match:
        return None
    return f"[{match.group(1)}] [{match.group(2)}]"


def payload_echo_confirmed(payload_text: str, echo_text: str) -> bool:
    marker = extract_payload_marker(payload_text)
    return bool(marker and f"PAYLOAD_ECHO: {marker} CONFIRMED" in echo_text or marker and f"{marker} CONFIRMED" in echo_text)


def extract_first_code_block(markdown_text: str) -> str:
    match = re.search(r"```\n(.*?)\n```", markdown_text, re.DOTALL)
    return match.group(1) if match else markdown_text


def infer_model_tier(model_name: str) -> ModelTier:
    name = model_name.lower()
    if any(
        token in name
        for token in ("gpt-5", "opus", "glm-5", "glm 5", "deepseek-r1", "deepseek r1", "qwen3", "qwen-3")
    ):
        return ModelTier.FRONTIER
    if any(token in name for token in ("sonnet", "gpt-4", "o3", "deepseek", "glm", "qwen", "gemini")):
        return ModelTier.HIGH
    if any(token in name for token in ("haiku", "mini", "small")):
        return ModelTier.MID
    if any(token in name for token in ("nano", "tiny")):
        return ModelTier.SMALL
    return ModelTier.UNKNOWN


def assess_model_parity(origin_model: str, partner_model: str) -> ModelParityCheck:
    origin_tier = infer_model_tier(origin_model)
    partner_tier = infer_model_tier(partner_model)
    if ModelTier.UNKNOWN in (origin_tier, partner_tier):
        return ModelParityCheck(
            origin=origin_model,
            partner=partner_model,
            delta=ModelDelta.MINOR,
            advisory="One or both model tiers are unknown. Treat parity as advisory and monitor dominance bias.",
        )
    gap = abs(origin_tier.value - partner_tier.value)
    if gap == 0:
        return ModelParityCheck(origin=origin_model, partner=partner_model, delta=ModelDelta.NONE)
    if gap == 1:
        return ModelParityCheck(
            origin=origin_model,
            partner=partner_model,
            delta=ModelDelta.MINOR,
            advisory="Slight analytical weight difference. Monitor for dominance bias.",
        )
    return ModelParityCheck(origin=origin_model, partner=partner_model, delta=ModelDelta.SIGNIFICANT)


def model_parity_halt_message(parity: ModelParityCheck) -> str:
    return "\n".join(
        [
            "MODEL PARITY GATE - HALT",
            "",
            "CONSENSUS HARDENING CANNOT PROCEED",
            "",
            "Model mismatch detected:",
            f"Origin: {parity.origin}",
            f"Partner: {parity.partner}",
            "Status: ASYMMETRIC",
            "Running this session would bias convergence, not test it.",
            "",
            "USER ACTION REQUIRED:",
            "-> Upgrade Origin to a comparable tier, OR",
            "-> Switch Partner to a comparable model, OR",
            "-> Accept asymmetry and log it as a structural constraint.",
            "",
            "SESSION PAUSED",
        ]
    )


def evaluate_r0_gate(*, core_problem: str, scope: tuple[str, ...], current_state: tuple[str, ...], worth_cost: bool) -> R0Gate:
    return R0Gate(
        solvable=("PASS", "harness negotiation can compare spec, evidence, and implementation constraints")
        if core_problem and core_problem != "UNKNOWN"
        else ("FATAL", "core problem is UNKNOWN"),
        scoped=("PASS", "scope is bounded for five rounds") if scope else ("FATAL", "scope is empty"),
        valid=("PASS", "current state provides external reality anchor") if current_state else ("FATAL", "current state is empty"),
        worth_it=("PASS", "cross-harness validation is worth the coordination cost")
        if worth_cost
        else ("FATAL", "decision does not justify cross-harness scaffolding overhead"),
    )


def classify_status(agreement: int, *, round_number: int, third_party_confirmed: bool = False) -> Status:
    if round_number >= 5 and agreement < 90:
        return Status.UNRESOLVED
    if agreement >= 90 and third_party_confirmed:
        return Status.LOCKED
    if agreement >= 90:
        return Status.PROVISIONAL_LOCK
    if agreement >= 80:
        return Status.PROVISIONAL
    return Status.EXPLORING


def build_session_declaration(session: CrossHarnessSession) -> str:
    return "\n".join(
        [
            "CROSS-HARNESS SCAFFOLDER INITIATED",
            f"Protocol: {CANONICAL_PROTOCOL_NAME} + {PROTOCOL_VERSION}",
            f"Origin System: {session.origin.system}",
            f"Origin Model: {session.origin.model}",
            f"Partner System: {session.partner.system}",
            f"Partner Model: {session.partner.model}",
            f"Validator Systems: {[profile.system for profile in session.validators] or 'NONE'}",
            f"Human Bridge: {session.human_bridge}",
            f"Phase: {session.phase.value} (Foundation)",
            f"Round: {session.round_number} of 5",
        ]
    )


def build_partner_shape_lock(phase: Phase = Phase.SPEC) -> str:
    if phase == Phase.FOUNDATION:
        body_contract = "Return exactly 2 sections: FOUNDATION_ATTACK and STATE_SNAPSHOT."
    else:
        body_contract = (
            "Return exactly 7 sections: ITEM_AGREEMENTS, WINNER_FRAMING, "
            "SCORING_TABLE, OBJECTIONS, FRAMEWORKS, CONVERGENCE_PLAN, STATE_SNAPSHOT."
        )
    return "\n".join(
        [
            "SHAPE_LOCK:",
            "- Reply as one code block with From:, To:, Subject: headers.",
            "- Wrap the entire response in BEGIN_PAYLOAD [RX] [6-alnum] and matching END_PAYLOAD.",
            f"- {body_contract}",
            "- Include PAYLOAD_ECHO in STATE_SNAPSHOT.",
            "- Pick one winner; no ties.",
            "- Include FLIP_CRITERIA for every PROVISIONAL item.",
            "- ASCII only.",
        ]
    )


def build_origin_packet(session: CrossHarnessSession, *, payload_id: str | None = None) -> str:
    errors = session.dossier.validate()
    if errors:
        raise ValueError("; ".join(errors))
    foundation_errors = session.foundation.validate() if session.foundation else ["foundation disclosure is required"]
    if foundation_errors:
        raise ValueError("; ".join(foundation_errors))

    parity = session.parity or assess_model_parity(session.origin.model, session.partner.model)
    if not parity.can_proceed:
        raise ValueError(model_parity_halt_message(parity))
    r0_gate = session.r0_gate or evaluate_r0_gate(
        core_problem=session.dossier.core_problem,
        scope=session.dossier.scope,
        current_state=session.dossier.current_state,
        worth_cost=True,
    )
    if r0_gate.status == "HALT":
        raise ValueError(r0_gate.render())

    participants = "\n".join(profile.render() for profile in session.participants)
    body = "\n\n".join(
        [
            f"From: {session.origin.system}",
            f"To: {session.partner.system}",
            "Subject: Cross-Harness Scaffolder - Phase 0 Round 0",
            "STYLE_GUIDE:\n- Tone: Calm, spec-like.\n- Framing: does not X unless Y.\n- Question: max 1; else UNKNOWN.\n- ASCII only.",
            session.context_check.render(),
            parity.render(),
            build_session_declaration(session),
            "HARNESS_PARTICIPANTS:\n" + participants,
            r0_gate.render(),
            session.foundation.render(),
            session.dossier.render(),
            "CROSS_HARNESS_DIAGNOSTICS:\n" + "\n".join(item.render() for item in session.diagnostics),
            build_partner_shape_lock(Phase.FOUNDATION),
        ]
    )
    envelope = PayloadEnvelope(body=body, payload_id=payload_id or "")

    return "\n\n".join(
        [
            "1. CORE_PROBLEM_STATEMENT",
            session.dossier.core_problem,
            "",
            "2. PARTNER_HARNESS_PACKET",
            "```",
            envelope.render(),
            "```",
            "",
            "3. TRANSMISSION_CHECKLIST",
            "[ ] R0 Gate passed",
            "[ ] Foundation >=70% (Phase 0)",
            "[ ] Prior received",
            "[ ] Objections addressed",
            "[ ] No skips",
            "[ ] Dossier updated",
            "[ ] Unknowns carried",
            "[ ] Blind spots acknowledged",
            "[ ] Structural vulnerabilities carried",
            "VERDICT: ITERATE (Phase 0 Round 0 of 5)",
        ]
    )


def build_partner_response_template(session: CrossHarnessSession, *, payload_id: str | None = None) -> str:
    envelope = PayloadEnvelope(
        payload_id=payload_id or "",
        body="\n\n".join(
            [
                f"From: {session.partner.system}",
                f"To: {session.origin.system}",
                "Subject: RE: Cross-Harness Scaffolder - Phase 0 Round 0",
                "FOUNDATION_ATTACK:",
                "ASSUMPTION_ATTACKS:",
                "1. [attack weakest assumption 1]",
                "2. [attack weakest assumption 2]",
                "3. [attack weakest assumption 3 or NONE]",
                "",
                "INVALIDATION_EXPLOITATION:",
                "1. [how invalidation condition 1 could trigger]",
                "2. [how invalidation condition 2 could trigger or NONE]",
                "",
                "VULNERABILITY_STRIKE:",
                "- [direct strike on key vulnerability]",
                "",
                "FOUNDATION_SCORE: [0-100%]",
                "ATTACK_SUMMARY: [2-3 sentences]",
                "",
                "STATE_SNAPSHOT:",
                f"PHASE: {session.phase.value}",
                f"ROUND: {session.round_number}/5",
                "STATUS: EXPLORING",
                "PAYLOAD_ECHO: [RX] [ORIGIN_ID] CONFIRMED",
                "FOUNDATION_SCORE: [0-100%]",
                "LOCKED: []",
                "PROVISIONAL: []",
                "PROVISIONAL_LOCK: []",
                "FLIP_ACTIVE: []",
                "BLIND_SPOTS_ACKNOWLEDGED:",
                "- Origin: []",
                "- Partner: []",
                "STRUCTURAL_VULNERABILITIES: []",
                "THIRD_PARTY_PENDING: []",
            ]
        ),
    )
    return envelope.render()


def build_implementation_handoff(session: CrossHarnessSession) -> str:
    validators = session.validators or (get_harness_profile("deepseek"),)
    return "\n".join(
        [
            "# Implementation Handoff",
            "",
            f"Session: {session.title}",
            f"Origin: {session.origin.system} ({session.origin.role})",
            f"Partner: {session.partner.system} ({session.partner.role})",
            f"Validators: {', '.join(profile.system for profile in validators)}",
            "",
            "## Harness Split",
            "",
            "Origin implementation harness owns:",
            *[f"- {item}" for item in (session.origin.strengths or ("repo edits", "tests", "build verification"))],
            "",
            "Partner adversary harness owns:",
            *[f"- {item}" for item in (session.partner.strengths or ("spec attack", "blind spot review", "third-party validation"))],
            "",
            "Validator harnesses own:",
            *[f"- {profile.system}: {', '.join(profile.best_for) or profile.role}" for profile in validators],
            "",
            "## Build Rules",
            "",
            "- Do not implement until Phase 1 is LOCKED or PROVISIONAL_LOCK with third-party entry test.",
            "- Keep database hot state compact: status, hashes, agreement, diagnostics, and validation pointers.",
            "- Store full packets once by content hash.",
            "- Run local tests before asking the partner for implementation QA.",
            "- Treat missing PAYLOAD_ECHO as retransmission, not disagreement.",
            "",
            "## Current Scope",
            *[f"- {item}" for item in session.dossier.scope],
        ]
    )


def build_compact_session_state(
    session: CrossHarnessSession,
    *,
    origin_packet: str,
    partner_template: str,
) -> str:
    state = {
        "protocol_version": PROTOCOL_VERSION,
        "canonical_protocol": {
            "name": CANONICAL_PROTOCOL_NAME,
            "url": CANONICAL_PROTOCOL_URL,
        },
        "title": session.title,
        "phase": session.phase.value,
        "round_number": session.round_number,
        "status": session.status.value,
        "participants": [
            {
                "system": profile.system,
                "model": profile.model,
                "role": profile.role,
                "best_for": list(profile.best_for),
            }
            for profile in session.participants
        ],
        "dossier_hash": content_hash(session.dossier.render()),
        "origin_packet_hash": content_hash(origin_packet),
        "partner_template_hash": content_hash(partner_template),
        "diagnostic_items": [diagnosis.item for diagnosis in session.diagnostics],
        "structural_vulnerabilities": list(session.structural_vulnerabilities),
        "token_budget": {
            "origin_packet_estimate": estimate_tokens(origin_packet),
            "partner_template_estimate": estimate_tokens(partner_template),
            "recommended_hot_state_budget": 900,
        },
    }
    return json.dumps(state, indent=2, sort_keys=True)


def build_database_blueprint() -> dict[str, Any]:
    return {
        "sql": DATABASE_BLUEPRINT_SQL,
        "strategy": "content_addressed_event_store",
        "token_efficiency": {
            "store_full_payload_once": True,
            "round_events_reference_content_hash": True,
            "state_snapshots_are_compact": True,
            "recommended_summary_budget_tokens": 900,
        },
        "scaling_notes": [
            "Use SQLite for local harness runs and Postgres for shared team deployment.",
            "Move payload_blobs.body to object storage when packets exceed repository audit budget.",
            "Index session_id, participant_id, phase, round_number, status, and third_party_status.",
            "Keep full transcript out of hot state; store hashes and compressed snapshots in round events.",
        ],
    }


def run_consensus_hardening_review(session: CrossHarnessSession, *, payload_id: str = "CHK001") -> ConsensusHardeningReport:
    findings: list[ConsensusFinding] = []

    def add(check: str, ok: bool, detail: str, severity: str = "critical") -> None:
        findings.append(ConsensusFinding(check, "PASS" if ok else "FAIL", detail, "info" if ok else severity))

    dossier_errors = session.dossier.validate()
    add("dossier", not dossier_errors, "; ".join(dossier_errors) if dossier_errors else "dossier is populated")

    foundation_errors = session.foundation.validate() if session.foundation else ["foundation disclosure is required"]
    add("foundation disclosure", not foundation_errors, "; ".join(foundation_errors) if foundation_errors else "foundation disclosure is complete")

    r0_gate = session.r0_gate or evaluate_r0_gate(
        core_problem=session.dossier.core_problem,
        scope=session.dossier.scope,
        current_state=session.dossier.current_state,
        worth_cost=True,
    )
    add("R0 gate", r0_gate.status == "PROCEED", r0_gate.render())

    parity = session.parity or assess_model_parity(session.origin.model, session.partner.model)
    add("model parity", parity.can_proceed, parity.render())

    unique_systems = {profile.system.lower() for profile in session.participants}
    add(
        "harness diversity",
        len(unique_systems) >= 2,
        f"{len(unique_systems)} unique harness systems present",
    )

    add(
        "third-party validator availability",
        bool(session.validators),
        "validator harnesses present" if session.validators else "add a validator harness before LOCKED status",
        severity="warning",
    )

    add(
        "decision diagnostics",
        bool(session.diagnostics),
        "diagnostic items present" if session.diagnostics else "at least one CrossHarnessDiagnosis is required",
    )

    try:
        origin_packet = build_origin_packet(session, payload_id=payload_id)
        payload = extract_first_code_block(origin_packet)
        add("payload envelope", validate_payload_envelope(payload), "origin packet has matching payload markers")
        add("ascii packet", ascii_only(origin_packet) == origin_packet, "origin packet is ASCII")
        add(
            "retired terminology",
            not any(term.lower() in origin_packet.lower() for term in RETIRED_TERMS),
            "generated packet avoids retired protocol terms",
        )
    except ValueError as exc:
        add("origin packet build", False, str(exc))

    failures = [finding for finding in findings if finding.status == "FAIL" and finding.severity == "critical"]
    warnings = [finding for finding in findings if finding.status == "FAIL" and finding.severity == "warning"]
    score = max(0, 100 - 15 * len(failures) - 5 * len(warnings))
    verdict = Verdict.PASS if not failures else Verdict.FAIL
    return ConsensusHardeningReport(verdict=verdict, score=score, findings=tuple(findings))


def build_scaffold_package(session: CrossHarnessSession, *, payload_id: str | None = None) -> ScaffoldPackage:
    origin_packet = build_origin_packet(session, payload_id=payload_id)
    partner_template = build_partner_response_template(session)
    handoff = build_implementation_handoff(session)
    compact_state = build_compact_session_state(
        session,
        origin_packet=origin_packet,
        partner_template=partner_template,
    )
    harness_profiles = json.dumps(
        {
            "available_harnesses": available_harnesses(),
            "participants": [
                {
                    "system": profile.system,
                    "model": profile.model,
                    "role": profile.role,
                    "strengths": list(profile.strengths),
                    "constraints": list(profile.constraints),
                    "default_tools": list(profile.default_tools),
                    "best_for": list(profile.best_for),
                }
                for profile in session.participants
            ],
        },
        indent=2,
        sort_keys=True,
    )
    review = run_consensus_hardening_review(session, payload_id=payload_id or "CHK001").render_markdown()
    readme = "\n".join(
        [
            "# Cross-Harness Scaffolder Bundle",
            "",
            f"Session: {session.title}",
            "",
            HARNESS_DEFINITION,
            "",
            "This bundle leverages different AI harness strengths to build efficient and scalable code:",
            f"- {session.origin.system}: implementation, tests, local verification.",
            f"- {session.partner.system}: adversarial spec review and blind-spot validation.",
            "- Validator harnesses: independent confirmation before lock.",
            "",
            "Artifacts:",
            "- `origin_packet.md`: copy to the partner harness.",
            "- `partner_response_template.md`: required partner response shape.",
            "- `implementation_handoff.md`: harness ownership and build rules.",
            "- `session_state.json`: compact resumable state with content hashes.",
            "- `schema.sql`: token-efficient event-store blueprint.",
            "- `harness_profiles.json`: participating harness capabilities.",
            "- `consensus_hardening_review.md`: CHP pass/fail review.",
        ]
    )
    artifacts = (
        ScaffoldArtifact("cross-harness/README.md", "bundle index", readme),
        ScaffoldArtifact("cross-harness/origin_packet.md", "origin packet for partner harness", origin_packet),
        ScaffoldArtifact("cross-harness/partner_response_template.md", "partner response shape lock", partner_template),
        ScaffoldArtifact("cross-harness/implementation_handoff.md", "implementation ownership and gates", handoff),
        ScaffoldArtifact("cross-harness/session_state.json", "compact resumable state", compact_state),
        ScaffoldArtifact("cross-harness/schema.sql", "content-addressed event-store schema", DATABASE_BLUEPRINT_SQL),
        ScaffoldArtifact("cross-harness/harness_profiles.json", "participant harness capabilities", harness_profiles),
        ScaffoldArtifact("cross-harness/consensus_hardening_review.md", "CHP validation report", review),
    )
    package = ScaffoldPackage(artifacts=artifacts)
    from .signing import attach_bundle_manifest

    return attach_bundle_manifest(package)


def write_scaffold_package(package: ScaffoldPackage, root: str | Path) -> tuple[Path, ...]:
    root_path = Path(root).resolve()
    root_path.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for artifact in package.artifacts:
        target = (root_path / artifact.path).resolve()
        if root_path not in target.parents and target != root_path:
            raise ValueError(f"artifact path escapes root: {artifact.path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(ascii_only(artifact.content), encoding="ascii")
        written.append(target)

    return tuple(written)
