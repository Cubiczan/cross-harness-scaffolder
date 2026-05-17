# Cross-Harness Scaffolder

Consensus-hardened scaffolding for using multiple AI coding harnesses to build efficient, scalable code.

Cross-Harness Scaffolder is a standalone Python package for coordinating work across AI coding systems and IDE harnesses such as Codex, Claude, Claude Code, GitHub Copilot, VS Code, Visual Studio, JetBrains Junie, Cursor, Windsurf, Zed, Kiro, Replit Agent, Continue, Cline, Roo Code, Aider, Sourcegraph Cody, Tabnine, Antigravity, GLM 5, DeepSeek, and Qwen. It does not try to make one model "the winner." It assigns each harness the work it is structurally best at, hardens the plan with Consensus Hardening Protocol gates, and emits compact artifacts that can move between tools without dragging full transcripts through every context window.

Canonical protocol source: [Consensus Hardening Protocol](https://codeberg.org/cubiczan/consensus-hardening-protocol)

Harness definition reference: [Arize AI, "What Is An Agent Harness? Definition, Tools, And Practical AI Use Cases"](https://arize.com/blog/what-is-an-agent-harness/)

## Why This Exists

Modern coding agents are not just model endpoints. They are harnesses: model configuration, tool loops, filesystem access, context management, approval rules, IDE indexing, browser capabilities, terminal execution, memory, and output validation wrapped around a model.

Those harnesses have different strengths:

| Harness | Strongest Use |
|---|---|
| Codex | Repo-local edits, tests, packaging, commit discipline |
| Claude | Spec attack, architecture critique, assumption finding |
| Claude Code | Codebase review, large-context implementation critique |
| GitHub Copilot | IDE-native completion, chat, agent mode, GitHub workflow handoff |
| VS Code | Extension host for Copilot, Continue, Cline, Roo Code, terminal/debug loops |
| Visual Studio | Enterprise .NET/C++ solution work, debugger/profiler-aware validation |
| JetBrains Junie | JetBrains project intelligence, JVM/polyglot refactors, autonomous IDE tasks |
| Cursor | IDE-native refactors, symbol-aware edits, developer review |
| Windsurf | AI-first multi-file feature work and flow-oriented coding sessions |
| Zed | Fast open-source editor loops and external agent coordination |
| Kiro | Spec-first development with agent hooks and implementation plans |
| Replit Agent | Browser-based app building, hosted workspace execution, checkpoint rollback |
| Continue | Open-source model-flexible IDE assistance for VS Code/JetBrains/CLI |
| Cline | Open-source IDE agent with file edits, terminal, browser, and MCP |
| Roo Code | Multi-mode VS Code agent workflows with custom modes and MCP |
| Aider | Git-aware terminal pair programming and patch-oriented edits |
| Sourcegraph Cody | Code graph context, large-codebase search, context-grounded explanations |
| Tabnine | Enterprise completion, privacy-oriented assistance, team policy controls |
| Antigravity | Agentic task execution, browser/workflow validation |
| GLM 5 | Independent frontier reasoning and multilingual critique |
| DeepSeek | Code reasoning, performance review, algorithm checks |
| Qwen | Code generation alternatives, broad implementation critique |
| SuperServe | Firecracker microVM validation, network-deny execution, release smoke checks |

Cross-Harness Scaffolder turns those differences into a repeatable build protocol.

## What It Does

Given a `CrossHarnessSession`, the package creates a handoff bundle that tells each harness:

- what decision is being made,
- what the goal state is,
- what assumptions must be attacked,
- which harness owns implementation,
- which harness owns adversarial review,
- which harnesses validate before lock,
- how payload integrity is checked,
- how compact state is persisted,
- how to avoid copying full transcripts across rounds.

It is designed for code work where correctness, cost, and scalability matter:

- architecture validation before implementation,
- database and event-store design,
- refactor planning,
- multi-harness code review,
- independent implementation QA,
- performance and edge-case review,
- package/repo scaffolding,
- release-gate preparation.

## Consensus Hardening Protocol

Cross-Harness Scaffolder uses Consensus Hardening Protocol ideas as the guardrail layer:

- R0 gate before work begins,
- foundation disclosure before implementation,
- adversarial foundation attack,
- model parity checks,
- payload envelopes with `PAYLOAD_ECHO`,
- status progression from `EXPLORING` to `PROVISIONAL_LOCK` to `LOCKED`,
- third-party validation before final lock,
- compact audit state,
- deterministic local review via `run_consensus_hardening_review()`.

The package ships its own local review helper. It is intentionally deterministic and dependency-free, so it can run in CI or before a handoff.

## Install

From the repo root:

```bash
python -m pip install -e .
```

Run tests:

```bash
python -m pytest -q
```

## CLI

The package installs a `chs` command for repeatable runs from YAML or JSON:

```bash
chs create-session --config examples/database_design.yaml --out .cross-harness-runs/database-design --payload-id ABC123
chs consensus-report --config examples/database_design.yaml --output .cross-harness-runs/database-design/report.md
chs export-schemas --out schemas
```

More detail: [docs/CLI_AND_EXAMPLES.md](docs/CLI_AND_EXAMPLES.md).

Commands:

- `create-session` builds the complete scaffold bundle from a session config.
- `consensus-report` runs a CI-ready Consensus Hardening report and exits nonzero if critical gates fail.
- `export-schemas` writes JSON schemas for session configs, packet objects, and compact state.

Example session bundles live in:

- `examples/database_design.yaml`
- `examples/refactor_review.yaml`
- `examples/package_release.yaml`

## Quick Start

```python
from cross_harness_scaffolder import (
    CrossHarnessDiagnosis,
    CrossHarnessDossier,
    CrossHarnessLayer,
    CrossHarnessSession,
    FoundationDisclosure,
    build_scaffold_package,
    get_harness_profile,
    run_consensus_hardening_review,
    write_scaffold_package,
)

session = CrossHarnessSession(
    title="Validate scalable event-store architecture",
    origin=get_harness_profile("codex", model="GPT-5.5"),
    partner=get_harness_profile("claude_code", model="Claude Opus 4.6"),
    validators=(
        get_harness_profile("cursor"),
        get_harness_profile("glm 5"),
        get_harness_profile("deepseek"),
        get_harness_profile("qwen3-coder"),
    ),
    human_bridge="Human operator",
    dossier=CrossHarnessDossier(
        core_problem="Validate whether the scaffolded event store supports efficient cross-harness code delivery.",
        goal_state=("scalable schema", "locked spec before implementation", "third-party validation"),
        current_state=("Standalone package uses Consensus Hardening Protocol gates.",),
        constraints=("ASCII packets", "compact state", "no full transcript duplication"),
        scope=("package API", "tests", "schema", "harness profiles"),
        origin_direction=("content-addressed payloads", "role-based harness ownership"),
    ),
    foundation=FoundationDisclosure(
        weakest_assumptions=(
            "Harnesses can preserve payload markers through copy and paste.",
            "Validator harnesses are sufficiently independent.",
        ),
        invalidation_conditions=(
            "A partner omits PAYLOAD_ECHO.",
            "Implementation begins before the spec is locked.",
        ),
        key_vulnerability="False agreement between harnesses before evidence is checked.",
    ),
    diagnostics=(
        CrossHarnessDiagnosis(
            item="database_architecture",
            observed_layer=CrossHarnessLayer.TASK_FLOW,
            constraint_layer=CrossHarnessLayer.SYSTEM_DESIGN,
            diagnosis="Schema drift is a system constraint, not a task typo.",
        ),
    ),
)

report = run_consensus_hardening_review(session)
assert report.passed

package = build_scaffold_package(session, payload_id="ABC123")
write_scaffold_package(package, "./.cross-harness-runs/run-001")
```

## Generated Bundle

`build_scaffold_package(session)` emits:

| Artifact | Purpose |
|---|---|
| `cross-harness/README.md` | Bundle index and harness split |
| `cross-harness/origin_packet.md` | Packet sent from origin harness to partner harness |
| `cross-harness/partner_response_template.md` | Required partner response shape |
| `cross-harness/implementation_handoff.md` | Implementation ownership and build rules |
| `cross-harness/session_state.json` | Compact resumable state with hashes |
| `cross-harness/schema.sql` | Token-efficient event-store blueprint |
| `cross-harness/harness_profiles.json` | Participating harness capabilities |
| `cross-harness/consensus_hardening_review.md` | Local Consensus Hardening review report |

The hot state stores hashes, summaries, participants, status, and diagnostics. Full packet bodies are stored once by content hash.

## API Overview

```python
from cross_harness_scaffolder import (
    available_harnesses,
    build_harness_council,
    build_origin_packet,
    build_scaffold_package,
    get_harness_profile,
    run_consensus_hardening_review,
)
```

Useful calls:

- `available_harnesses()` lists built-in harness profiles.
- `get_harness_profile("qwen3-coder")` resolves aliases to a profile.
- `build_harness_council("codex", "claude code", "cursor", "deepseek")` creates a participant set.
- `build_origin_packet(session)` emits the origin-to-partner packet.
- `run_consensus_hardening_review(session)` returns pass/fail findings.
- `build_scaffold_package(session)` creates the complete handoff bundle.
- `load_session("examples/database_design.yaml")` creates a session from YAML or JSON.
- `export_json_schemas("schemas")` exports config, packet, and state schemas.

## Adapter Layer

The optional adapter layer gives live integrations a stable seam without making the core package depend on every IDE or vendor SDK.

```python
from cross_harness_scaffolder import FileHarnessAdapter, get_harness_profile

adapter = FileHarnessAdapter(get_harness_profile("cursor"), ".cross-harness-live")
adapter.send_packet("BEGIN_PAYLOAD [RX] [ABC123]\n...\nEND_PAYLOAD [RX] [ABC123]", session_id="run-001")
response = adapter.receive_response(session_id="run-001")
```

`FileHarnessAdapter` is intentionally simple: it writes `inbox_packet.md` and reads `outbox_response.md`. Native adapters for Codex, Claude Code, Cursor, Copilot, Antigravity, GLM 5, DeepSeek, Qwen, and SuperServe can use the same interface.

## Built-In Aliases

The profile resolver accepts common names:

| Alias | Profile |
|---|---|
| `openai`, `gpt` | Codex |
| `anthropic` | Claude |
| `claude code`, `claude-code` | Claude Code |
| `copilot`, `github copilot`, `gh copilot` | GitHub Copilot |
| `vs code`, `visual studio code`, `vsc` | VS Code |
| `vs`, `microsoft visual studio` | Visual Studio |
| `jetbrains`, `junie`, `jetbrains ai` | JetBrains Junie |
| `cursor ide` | Cursor |
| `windsurf ai`, `codeium` | Windsurf |
| `zed editor` | Zed |
| `aws kiro` | Kiro |
| `replit`, `replit ai` | Replit Agent |
| `continue.dev`, `continue dev` | Continue |
| `roo`, `roo-code`, `roo code` | Roo Code |
| `sourcegraph`, `cody`, `sourcegraph amp` | Sourcegraph Cody |
| `google antigravity` | Antigravity |
| `glm 5`, `glm-5`, `zhipu` | GLM 5 |
| `deepseek r1`, `deepseek-r1` | DeepSeek |
| `qwen3`, `qwen3-coder`, `qwen coder`, `tongyi` | Qwen |
| `firecracker`, `microvm`, `superserve.ai` | SuperServe |

## Token-Efficient State

The persistence blueprint is designed for repeated harness passes without transcript bloat:

- `cross_harness_sessions` stores one hot session row.
- `cross_harness_participants` stores each harness role and capability set.
- `cross_harness_items` stores compact decision state and diagnostics.
- `cross_harness_payload_blobs` stores full packets once by hash.
- `cross_harness_round_events` references packet hashes and state snapshots.
- `cross_harness_validations` stores third-party validation records.

This lets teams resume a run from compact state while keeping full payloads auditable.

## Infrastructure Backends

The package includes dependency-light infrastructure seams:

- `SQLiteStore` for local runs and test fixtures.
- `PostgresStore` for shared production session state.
- `CockroachStore` for distributed state with serializable retry guidance.
- `LocalExecutionBackend` for trusted local or CI commands.
- `SuperserveBackend` for SuperServe-style Firecracker microVM validation.

See [docs/INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md).

## Repo Discovery Intake

Use [github_repo_classifier](https://github.com/chriscarrollsmith/github_repo_classifier) as a separate discovery pipeline to find underrated harness, database, sandbox, and developer-tooling repos. Cross-Harness Scaffolder records the leverage matrix in [docs/REPO_LEVERAGE_MATRIX.md](docs/REPO_LEVERAGE_MATRIX.md) and keeps attribution in [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

## Safety Model

Cross-Harness Scaffolder is a coordination and validation scaffold. It does not grant tools, spend money, sign contracts, push code, or run external APIs on its own.

Recommended operating rules:

- Never let the same harness self-certify final lock.
- Keep implementation blocked until the spec is locked or provisionally locked with validator entry.
- Treat missing `PAYLOAD_ECHO` as retransmission, not disagreement.
- Keep secrets outside harness packets.
- Preserve a human release decision for irreversible external actions.
- Run local tests before asking another harness for implementation QA.

## Development

```bash
python -m pip install -e .
python -m pytest -q
python -m compileall src
```

The test suite covers:

- requested harness profiles, including GLM 5, DeepSeek, and Qwen,
- SuperServe as a Firecracker validation harness and execution backend seam,
- alias resolution,
- model parity,
- payload envelopes,
- Consensus Hardening review,
- YAML/JSON session loading,
- CLI bundle/report/schema commands,
- JSON schema exports,
- file-based adapter handoff,
- token-efficient package output,
- path traversal protection.

## Roadmap

- Native live adapters for selected harnesses where APIs are stable and permission models are clear.
- Schema validation command that validates a config before bundle creation.
- GitHub Actions examples for `chs consensus-report`.
- Signed bundle manifests for release-gate audit trails.

## Repository Status

This repo is standalone. It is not a Cubiczan Swarm Pack update.

Current local state:

- Python package scaffolded.
- Tests passing.
- Consensus Hardening review included.
- CLI, schemas, adapters, and example session bundles included.
- PostgreSQL, CockroachDB, SQLite, local execution, and SuperServe adapter seams included.
- Published to Codeberg and GitHub mirrors where credentials are configured.
