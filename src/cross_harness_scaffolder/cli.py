"""Command line interface for Cross-Harness Scaffolder."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .core import build_scaffold_package, run_consensus_hardening_review, write_scaffold_package
from .schemas import export_json_schemas
from .session_config import load_session
from .signing import sign_scaffold_package, write_signed_directory_manifest
from .validation import validate_session_config


def _create_session(args: argparse.Namespace) -> int:
    validation = validate_session_config(args.config)
    if not validation.ok:
        print(validation.render_markdown())
        return 1
    session = load_session(args.config)
    package = build_scaffold_package(session, payload_id=args.payload_id)
    if args.signing_key_env:
        secret = os.environ.get(args.signing_key_env)
        if not secret:
            print(f"missing signing secret env var: {args.signing_key_env}")
            return 1
        package = sign_scaffold_package(package, secret, key_id=args.key_id, signer=args.signer)
    written = write_scaffold_package(package, args.out)
    print(json.dumps({"written": [str(path) for path in written], "artifact_count": len(written)}, indent=2))
    return 0


def _consensus_report(args: argparse.Namespace) -> int:
    session = load_session(args.config)
    report = run_consensus_hardening_review(session, payload_id=args.payload_id)
    output = report.render_markdown() if args.format == "markdown" else json.dumps(
        {
            "verdict": report.verdict.value,
            "score": report.score,
            "findings": [finding.__dict__ for finding in report.findings],
        },
        indent=2,
    )
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output, encoding="ascii")
    else:
        print(output)
    return 0 if report.passed else 1


def _validate_config(args: argparse.Namespace) -> int:
    result = validate_session_config(args.config)
    output = result.render_markdown() if args.format == "markdown" else result.render_json()
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output, encoding="ascii")
    else:
        print(output)
    return 0 if result.ok else 1


def _export_schemas(args: argparse.Namespace) -> int:
    written = export_json_schemas(args.out)
    print(json.dumps({"written": [str(path) for path in written]}, indent=2))
    return 0


def _sign_bundle(args: argparse.Namespace) -> int:
    secret = os.environ.get(args.secret_env)
    if not secret:
        print(f"missing signing secret env var: {args.secret_env}")
        return 1
    output = args.output or str(Path(args.bundle) / "bundle_manifest.json")
    target = write_signed_directory_manifest(args.bundle, output, secret, key_id=args.key_id, signer=args.signer)
    print(json.dumps({"written": str(target), "key_id": args.key_id}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chs", description="Cross-Harness Scaffolder CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create-session", help="Create a scaffold bundle from YAML or JSON config")
    create.add_argument("--config", required=True, help="Path to session YAML or JSON")
    create.add_argument("--out", required=True, help="Output directory")
    create.add_argument("--payload-id", default=None, help="Optional 6-character payload id")
    create.add_argument("--signing-key-env", help="Environment variable containing an HMAC signing secret")
    create.add_argument("--key-id", default="local", help="Signing key identifier for the bundle manifest")
    create.add_argument("--signer", default="cross-harness-scaffolder", help="Signer label stored in manifests")
    create.set_defaults(func=_create_session)

    validate = sub.add_parser("validate-config", help="Validate a session config before bundle creation")
    validate.add_argument("--config", required=True, help="Path to session YAML or JSON")
    validate.add_argument("--format", choices=("markdown", "json"), default="markdown")
    validate.add_argument("--output", help="Optional validation report output path")
    validate.set_defaults(func=_validate_config)

    report = sub.add_parser("consensus-report", help="Run a CI-ready Consensus Hardening report")
    report.add_argument("--config", required=True, help="Path to session YAML or JSON")
    report.add_argument("--output", help="Optional report output path")
    report.add_argument("--format", choices=("markdown", "json"), default="markdown")
    report.add_argument("--payload-id", default="CI0001", help="Payload id used for deterministic packet checks")
    report.set_defaults(func=_consensus_report)

    schemas = sub.add_parser("export-schemas", help="Export JSON schemas")
    schemas.add_argument("--out", required=True, help="Output directory")
    schemas.set_defaults(func=_export_schemas)

    sign = sub.add_parser("sign-bundle", help="Write a signed release-gate manifest for an existing bundle")
    sign.add_argument("--bundle", required=True, help="Bundle directory to sign, usually out/cross-harness")
    sign.add_argument("--output", help="Manifest output path, default is bundle/bundle_manifest.json")
    sign.add_argument("--secret-env", default="CHS_SIGNING_KEY", help="Environment variable containing signing secret")
    sign.add_argument("--key-id", required=True, help="Signing key identifier")
    sign.add_argument("--signer", default="cross-harness-scaffolder", help="Signer label stored in manifests")
    sign.set_defaults(func=_sign_bundle)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
