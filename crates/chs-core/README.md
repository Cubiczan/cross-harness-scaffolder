# CHS Core

`chs-core` is the native Rust core for Cross-Harness Scaffolder. It provides deterministic
session config validation, Consensus Hardening reports, payload envelope checks, content-addressed
artifact manifests, HMAC release-gate signing, and transparency log entries.

The crate is intentionally credential-free. Signing secrets are passed by the caller at runtime,
usually from an environment variable such as `CHS_SIGNING_KEY`; secrets must never be committed.
