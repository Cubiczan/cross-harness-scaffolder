# Consensus Hardening Review

This standalone repository was shaped against the Consensus Hardening Protocol source at:

https://codeberg.org/cubiczan/consensus-hardening-protocol

## Applied Gates

- R0 gate: implemented by `evaluate_r0_gate()`.
- Foundation disclosure: implemented by `FoundationDisclosure.validate()`.
- Foundation attack threshold: implemented by `FoundationAttack.verdict()`.
- Model parity: implemented by `assess_model_parity()`.
- Payload integrity: implemented by `PayloadEnvelope`, `validate_payload_envelope()`, and `payload_echo_confirmed()`.
- Lock progression: implemented by `classify_status()`.
- Third-party validation requirement: enforced as a Consensus Hardening warning until a validator harness is present.
- Compact audit state: implemented by `build_compact_session_state()` and the event-store schema.

## Harness Expansion Check

The standalone package supports these harness families as first-class profiles:

- Codex
- Claude
- Claude Code
- Cursor
- Antigravity
- GLM 5
- DeepSeek
- Qwen

Each harness can be origin, partner, or validator depending on the work split. The recommended pattern for production work is:

- Origin: implementation harness that owns repo edits and tests.
- Partner: adversarial harness that attacks the spec before implementation.
- Validators: one or more independent harnesses that confirm the lock before final status.

## Current Verdict

PASS for local package scaffold.

Residual risk: final production locks still require real third-party review by a separate harness or human reviewer.
