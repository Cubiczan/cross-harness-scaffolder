import json
from pathlib import Path

from cross_harness_scaffolder import (
    FileHarnessAdapter,
    HarnessAdapterRegistry,
    export_json_schemas,
    get_harness_profile,
    load_session,
    schema_bundle,
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

    assert main(["consensus-report", "--config", str(config), "--output", str(report)]) == 0
    assert "Verdict: PASS" in report.read_text(encoding="ascii")


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


def test_adapter_registry() -> None:
    registry = HarnessAdapterRegistry()
    adapter = FileHarnessAdapter(get_harness_profile("codex"), ".")

    registry.register("codex", adapter)

    assert registry.names() == ("codex",)
    assert registry.get("CODEX") is adapter
