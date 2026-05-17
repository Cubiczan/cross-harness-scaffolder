import json
import sys
from pathlib import Path

from cross_harness_scaffolder import (
    AdapterStability,
    CommandHarnessAdapter,
    FileHarnessAdapter,
    HarnessAdapterRegistry,
    build_scaffold_package,
    export_json_schemas,
    get_harness_profile,
    json_schema_validator_available,
    load_session,
    native_adapter_specs,
    schema_bundle,
    sign_bundle_manifest_public_key,
    sign_scaffold_package,
    sign_scaffold_package_public_key,
    stable_native_adapter_specs,
    validate_session_config,
    verify_bundle_manifest_public_key,
    verify_bundle_manifest_signature,
)
from cross_harness_scaffolder.cli import main


def _config(path: Path) -> Path:
    data = {
        "title": "CLI session",
        "human_bridge": "Tester",
        "origin": {"name": "codex", "model": "GPT-5.5"},
        "partner": {"name": "claude_code", "model": "Claude Opus 4.6"},
        "validators": [{"name": "deepseek"}],
        "dossier": {
            "core_problem": "Validate CLI scaffold creation.",
            "goal_state": ["bundle written", "report passes"],
            "current_state": ["JSON config drives session creation."],
            "constraints": ["ASCII packets", "compact state"],
            "scope": ["CLI", "schemas"],
            "origin_direction": ["write bundle"],
        },
        "foundation": {
            "weakest_assumptions": ["JSON config represents YAML-equivalent structure."],
            "invalidation_conditions": ["payload build fails"],
            "key_vulnerability": "CLI drift from package API.",
        },
        "diagnostics": [
            {
                "item": "cli",
                "observed_layer": "task_flow",
                "constraint_layer": "system_design",
                "diagnosis": "CLI behavior must stay thin over API behavior.",
            }
        ],
    }
    path.write_text(json.dumps(data), encoding="ascii")
    return path


def test_load_session_from_json_config(tmp_path: Path) -> None:
    session = load_session(_config(tmp_path / "session.json"))

    assert session.title == "CLI session"
    assert session.origin.system == "Codex"
    assert session.validators[0].system == "DeepSeek"


def test_cli_create_session_and_consensus_report(tmp_path: Path) -> None:
    config = _config(tmp_path / "session.json")
    out = tmp_path / "bundle"
    report = tmp_path / "report.md"

    assert main(["create-session", "--config", str(config), "--out", str(out), "--payload-id", "ABC123"]) == 0
    assert (out / "cross-harness" / "origin_packet.md").exists()
    assert (out / "cross-harness" / "bundle_manifest.json").exists()

    assert main(["consensus-report", "--config", str(config), "--output", str(report)]) == 0
    assert "Verdict: PASS" in report.read_text(encoding="ascii")


def test_cli_validate_config_and_reject_invalid_config(tmp_path: Path) -> None:
    config = _config(tmp_path / "session.json")
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps({"title": "bad"}), encoding="ascii")

    assert main(["validate-config", "--config", str(config)]) == 0
    assert main(["validate-config", "--config", str(invalid), "--format", "json"]) == 1
    assert not validate_session_config(invalid).ok


def test_cli_validate_config_with_optional_json_schema(tmp_path: Path) -> None:
    config = _config(tmp_path / "session.json")
    result = validate_session_config(config, use_json_schema=True)

    assert result.ok
    if not json_schema_validator_available():
        assert any(issue.path == "json_schema" and issue.severity == "warning" for issue in result.issues)


def test_cli_create_session_with_signed_manifest(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path / "session.json")
    out = tmp_path / "signed-bundle"
    monkeypatch.setenv("CHS_TEST_SIGNING_KEY", "secret")

    assert (
        main(
            [
                "create-session",
                "--config",
                str(config),
                "--out",
                str(out),
                "--payload-id",
                "ABC123",
                "--signing-key-env",
                "CHS_TEST_SIGNING_KEY",
                "--key-id",
                "test-key",
            ]
        )
        == 0
    )

    manifest = json.loads((out / "cross-harness" / "bundle_manifest.json").read_text(encoding="ascii"))
    assert manifest["signature"]["key_id"] == "test-key"
    assert verify_bundle_manifest_signature(manifest, "secret")


def test_cli_sign_bundle_command(tmp_path: Path, monkeypatch) -> None:
    config = _config(tmp_path / "session.json")
    out = tmp_path / "bundle"
    monkeypatch.setenv("CHS_SIGNING_KEY", "secret")

    assert main(["create-session", "--config", str(config), "--out", str(out), "--payload-id", "ABC123"]) == 0
    assert main(["sign-bundle", "--bundle", str(out / "cross-harness"), "--key-id", "release-key"]) == 0

    manifest = json.loads((out / "cross-harness" / "bundle_manifest.json").read_text(encoding="ascii"))
    assert manifest["signature"]["key_id"] == "release-key"
    assert verify_bundle_manifest_signature(manifest, "secret")


def test_cli_export_schemas(tmp_path: Path) -> None:
    assert main(["export-schemas", "--out", str(tmp_path)]) == 0

    assert (tmp_path / "session_config.schema.json").exists()
    assert (tmp_path / "packet.schema.json").exists()
    assert (tmp_path / "state.schema.json").exists()


def test_schema_bundle_exports_expected_schemas(tmp_path: Path) -> None:
    bundle = schema_bundle()
    written = export_json_schemas(tmp_path)

    assert {"session_config.schema.json", "packet.schema.json", "state.schema.json"} == set(bundle)
    assert len(written) == 3


def test_file_harness_adapter_round_trip(tmp_path: Path) -> None:
    adapter = FileHarnessAdapter(get_harness_profile("cursor"), tmp_path)
    result = adapter.send_packet("hello", session_id="session-1")

    assert result.ok
    assert result.artifact_path is not None
    outbox = Path(result.artifact_path).with_name("outbox_response.md")
    outbox.write_text("response", encoding="ascii")
    assert adapter.receive_response(session_id="session-1") == "response"


def test_command_harness_adapter_round_trip() -> None:
    adapter = CommandHarnessAdapter(
        get_harness_profile("codex"),
        (
            sys.executable,
            "-c",
            "import sys; print(sys.stdin.read().upper())",
        ),
    )

    result = adapter.send_packet("payload", session_id="session-1")

    assert result.ok
    assert adapter.receive_response(session_id="session-1").strip() == "PAYLOAD"


def test_native_adapter_specs_name_permission_boundaries() -> None:
    specs = {spec.name: spec for spec in native_adapter_specs()}

    assert {
        "file-handoff",
        "codex-cli",
        "claude-code-cli",
        "aider-cli",
        "superserve-execution",
        "cursor-cli",
        "continue-cli",
        "cline-file-handoff",
        "roo-code-file-handoff",
        "copilot-cli",
        "sourcegraph-cody-cli",
        "glm-cli",
        "deepseek-cli",
        "qwen-cli",
    } <= set(specs)
    assert "explicit local command tuple" in specs["codex-cli"].permission_boundary
    assert specs["continue-cli"].stability == AdapterStability.GATED
    assert {spec.name for spec in stable_native_adapter_specs()} <= set(specs)


def test_adapter_registry() -> None:
    registry = HarnessAdapterRegistry()
    adapter = FileHarnessAdapter(get_harness_profile("codex"), ".")

    registry.register("codex", adapter)

    assert registry.names() == ("codex",)
    assert registry.get("CODEX") is adapter


def test_sign_scaffold_package_verifies_manifest(tmp_path: Path) -> None:
    session = load_session(_config(tmp_path / "session.json"))
    package = sign_scaffold_package(build_scaffold_package(session, payload_id="ABC123"), "secret", key_id="unit")
    manifest = json.loads(next(item for item in package.artifacts if item.path.endswith("bundle_manifest.json")).content)

    assert manifest["artifact_count"] == 8
    assert verify_bundle_manifest_signature(manifest, "secret")


def test_public_key_signing_optional_dependency(tmp_path: Path) -> None:
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
    except ImportError:
        try:
            sign_bundle_manifest_public_key({"manifest_version": "test"}, "not-a-key", key_id="ed-key")
        except RuntimeError as exc:
            assert "crypto extra" in str(exc)
        else:
            raise AssertionError("expected missing crypto extra to raise")
        return

    session = load_session(_config(tmp_path / "session.json"))
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    package = sign_scaffold_package_public_key(
        build_scaffold_package(session, payload_id="ABC123"),
        private_pem,
        key_id="ed-key",
    )
    manifest = json.loads(next(item for item in package.artifacts if item.path.endswith("bundle_manifest.json")).content)

    assert manifest["signature"]["algorithm"] == "ed25519"
    assert verify_bundle_manifest_public_key(manifest, public_pem)
