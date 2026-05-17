# CLI And Examples

Cross-Harness Scaffolder can be driven from YAML or JSON so teams can store repeatable harness sessions beside the code they are validating.

## Commands

```bash
chs create-session --config examples/database_design.yaml --out .cross-harness-runs/database-design --payload-id ABC123
chs validate-config --config examples/database_design.yaml
chs consensus-report --config examples/database_design.yaml --output .cross-harness-runs/database-design/report.md
chs export-schemas --out schemas
CHS_SIGNING_KEY="change-me" chs sign-bundle --bundle .cross-harness-runs/database-design/cross-harness --key-id local-release
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

Use `chs validate-config` and `chs consensus-report` as pre-merge checks. Validation catches malformed session configs before bundle creation. The report fails on critical Consensus Hardening issues such as missing foundation disclosure, invalid R0 gate, model parity halt, malformed payload envelope, or absent diagnostic items.

```bash
chs consensus-report --config examples/package_release.yaml --format json --output chs-report.json
```

Warnings, such as missing third-party validators, reduce the score without failing the command. Critical findings fail the command.

See `docs/github-actions/consensus-hardening.yml` for a matrix job that validates each example config and uploads the report artifact. Copy it to `.github/workflows/consensus-hardening.yml` when publishing with a token that has GitHub workflow permission.

## Live Adapter Seam

The adapter interface is deliberately small:

- `send_packet(packet, session_id=...)`
- `receive_response(session_id=...)`

`FileHarnessAdapter` is the baseline bridge for any harness that can read and write files. Native adapters can wrap APIs or IDE automation while preserving the same audit and packet contracts.

`CommandHarnessAdapter` is the baseline live adapter for local CLI harnesses. It never invokes a shell. The caller passes an explicit command tuple, the packet goes to stdin, stdout becomes the response, and timeout/output caps keep the permission boundary clear.

## Signed Manifests

Every generated bundle includes `cross-harness/bundle_manifest.json`. Use HMAC signing for release gates:

```bash
CHS_SIGNING_KEY="change-me" chs create-session --config examples/package_release.yaml --out .cross-harness-runs/release --signing-key-env CHS_SIGNING_KEY --key-id release-key
```

or sign an existing bundle:

```bash
CHS_SIGNING_KEY="change-me" chs sign-bundle --bundle .cross-harness-runs/release/cross-harness --key-id release-key
```

The manifest records artifact paths, purposes, content hashes, token estimates, signer, key id, and signature algorithm.
