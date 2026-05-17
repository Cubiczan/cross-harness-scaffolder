# CLI And Examples

Cross-Harness Scaffolder can be driven from YAML or JSON so teams can store repeatable harness sessions beside the code they are validating.

## Commands

```bash
chs create-session --config examples/database_design.yaml --out .cross-harness-runs/database-design --payload-id ABC123
chs consensus-report --config examples/database_design.yaml --output .cross-harness-runs/database-design/report.md
chs export-schemas --out schemas
```

## Session Config Shape

Required top-level fields:

- `title`
- `origin`
- `partner`
- `dossier`
- `foundation`
- `diagnostics`

Optional fields:

- `human_bridge`
- `validators`

Profiles are resolved through the built-in harness registry, so configs can use aliases such as `claude code`, `github copilot`, `glm-5`, `qwen coder`, or `firecracker`.

## Example Bundles

- `database_design.yaml`: validates PostgreSQL/CockroachDB-ready schema design before implementation.
- `refactor_review.yaml`: splits refactor work between implementation, spec attack, and validator harnesses.
- `package_release.yaml`: adds release review with SuperServe Firecracker-style sandbox validation.

## CI Gate

Use `chs consensus-report` as a pre-merge check. It fails on critical Consensus Hardening issues such as missing foundation disclosure, invalid R0 gate, model parity halt, malformed payload envelope, or absent diagnostic items.

```bash
chs consensus-report --config examples/package_release.yaml --format json --output chs-report.json
```

Warnings, such as missing third-party validators, reduce the score without failing the command. Critical findings fail the command.

## Live Adapter Seam

The adapter interface is deliberately small:

- `send_packet(packet, session_id=...)`
- `receive_response(session_id=...)`

`FileHarnessAdapter` is the baseline bridge for any harness that can read and write files. Native adapters can wrap APIs or IDE automation while preserving the same audit and packet contracts.
