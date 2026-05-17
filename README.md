# Cross-Harness Scaffolder

Cross-Harness Scaffolder is a standalone, Consensus Hardening Protocol guided package for using multiple AI coding harnesses to build efficient and scalable code.

The core idea is simple: each harness has different operating strengths. Codex may own repo-local edits and tests. Claude or Claude Code may attack the spec. Cursor may handle IDE-native refactors. Antigravity may run broader agentic tasks. GLM 5, DeepSeek, and Qwen can act as lower-correlation frontier reviewers or implementation challengers for architecture, algorithm, multilingual, or performance checks.

Canonical protocol source: [Consensus Hardening Protocol](https://codeberg.org/cubiczan/consensus-hardening-protocol)

Harness definition reference: [Arize AI, "What Is An Agent Harness? Definition, Tools, And Practical AI Use Cases"](https://arize.com/blog/what-is-an-agent-harness/)

## Included Harness Profiles

- Codex
- Claude
- Claude Code
- Cursor
- Antigravity
- GLM 5
- DeepSeek
- Qwen

Each profile captures:

- system name and configured model
- role in the scaffold
- strengths and constraints
- default tool surfaces
- best-fit work ownership

## What It Produces

`build_scaffold_package(session)` emits a compact handoff bundle:

- `cross-harness/README.md`
- `cross-harness/origin_packet.md`
- `cross-harness/partner_response_template.md`
- `cross-harness/implementation_handoff.md`
- `cross-harness/session_state.json`
- `cross-harness/schema.sql`
- `cross-harness/harness_profiles.json`
- `cross-harness/consensus_hardening_review.md`

The session state stores hashes and summaries, not full transcripts. Full packet bodies are content-addressed once.

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
    human_bridge="Shyam",
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
            "The validator harnesses are sufficiently independent.",
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

## Consensus Hardening Checks

`run_consensus_hardening_review()` checks:

- dossier completeness
- foundation disclosure completeness
- R0 gate
- model parity
- harness diversity
- third-party validator availability
- decision diagnostics
- payload envelope integrity
- ASCII packet safety
- retired terminology avoidance

The review is intentionally local and deterministic. It does not replace a human release decision or a real third-party validation step before locked production changes.

## Repository Status

This repo is standalone. It is not a Cubiczan Swarm Pack update.
