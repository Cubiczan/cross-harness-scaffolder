import json
import re
from pathlib import Path

from cross_harness_scaffolder import (
    CANONICAL_PROTOCOL_NAME,
    CANONICAL_PROTOCOL_URL,
    CrossHarnessDiagnosis,
    CrossHarnessDossier,
    CrossHarnessLayer,
    CrossHarnessSession,
    FoundationAttack,
    FoundationDisclosure,
    ModelDelta,
    Status,
    available_harnesses,
    assess_model_parity,
    build_database_blueprint,
    build_harness_council,
    build_origin_packet,
    build_scaffold_package,
    classify_status,
    content_hash,
    get_harness_profile,
    payload_echo_confirmed,
    run_consensus_hardening_review,
    validate_payload_envelope,
    write_scaffold_package,
)


def _session() -> CrossHarnessSession:
    return CrossHarnessSession(
        title="Validate cross-harness database architecture",
        origin=get_harness_profile("codex", model="GPT-5.5"),
        partner=get_harness_profile("claude_code", model="Claude Opus 4.6"),
        validators=(
            get_harness_profile("cursor"),
            get_harness_profile("glm 5"),
            get_harness_profile("deepseek"),
        ),
        human_bridge="Shyam",
        dossier=CrossHarnessDossier(
            core_problem="Validate whether a content-addressed event store supports scalable cross-harness code delivery.",
            goal_state=(">=90% agreement before implementation", "third-party validation before LOCKED"),
            current_state=("Standalone repo has Consensus Hardening Protocol gates.",),
            constraints=("Max five rounds", "ASCII payloads", "No full transcript duplication in hot state"),
            scope=("Package API, docs, tests, and database blueprint",),
            origin_direction=("Use content-addressed payload bodies", "Keep state snapshots compact"),
        ),
        foundation=FoundationDisclosure(
            weakest_assumptions=(
                "Harnesses can preserve PAYLOAD markers through copy and paste.",
                "Validator harnesses remain independent enough to reduce correlated failure.",
            ),
            invalidation_conditions=(
                "Partner omits PAYLOAD_ECHO.",
                "Implementation begins before spec lock.",
            ),
            key_vulnerability="False agreement caused by harnesses optimizing for speed over evidence.",
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


def test_harness_profiles_include_requested_systems() -> None:
    names = {get_harness_profile(name).system for name in available_harnesses()}

    assert {"Codex", "Claude", "Claude Code", "Cursor", "Antigravity", "GLM 5", "DeepSeek"} <= names


def test_aliases_build_requested_harness_council() -> None:
    council = build_harness_council("codex", "claude code", "cursor", "glm-5", "deepseek-r1")
    systems = [profile.system for profile in council]

    assert systems == ["Codex", "Claude Code", "Cursor", "GLM 5", "DeepSeek"]


def test_model_parity_allows_frontier_pair_and_blocks_large_gap() -> None:
    frontier = assess_model_parity("GLM-5", "DeepSeek-R1")
    mismatch = assess_model_parity("Claude Haiku", "GPT-5.5")

    assert frontier.delta == ModelDelta.NONE
    assert frontier.can_proceed
    assert mismatch.delta == ModelDelta.SIGNIFICANT
    assert not mismatch.can_proceed


def test_origin_packet_uses_cross_harness_language_and_payload_echo() -> None:
    packet = build_origin_packet(_session(), payload_id="ABC123")

    assert packet.count("1. CORE_PROBLEM_STATEMENT") == 1
    assert packet.count("2. PARTNER_HARNESS_PACKET") == 1
    assert packet.count("3. TRANSMISSION_CHECKLIST") == 1
    assert "CROSS_HARNESS_DIAGNOSTICS:" in packet
    assert "CROSS-HARNESS SCAFFOLDER INITIATED" in packet
    assert "GLM 5" in packet
    assert "DeepSeek" in packet
    assert ("triang" + "ulat") not in packet.lower()
    assert packet.encode("ascii").decode("ascii") == packet

    payload = re.search(r"```\n(.*?)\n```", packet, re.DOTALL)
    assert payload
    assert validate_payload_envelope(payload.group(1))
    assert payload_echo_confirmed(payload.group(1), "[RX] [ABC123] CONFIRMED")


def test_consensus_hardening_review_passes_with_validator_harnesses() -> None:
    report = run_consensus_hardening_review(_session(), payload_id="ABC123")

    assert report.passed
    assert report.score == 100
    assert CANONICAL_PROTOCOL_NAME == "Consensus Hardening Protocol"
    assert CANONICAL_PROTOCOL_URL == "https://codeberg.org/cubiczan/consensus-hardening-protocol"


def test_consensus_hardening_review_warns_without_validator() -> None:
    base = _session()
    no_validator = CrossHarnessSession(
        title=base.title,
        origin=base.origin,
        partner=base.partner,
        human_bridge=base.human_bridge,
        dossier=base.dossier,
        foundation=base.foundation,
        diagnostics=base.diagnostics,
    )

    report = run_consensus_hardening_review(no_validator, payload_id="ABC123")

    assert report.passed
    assert report.score == 95
    assert any(finding.check == "third-party validator availability" for finding in report.findings)


def test_foundation_attack_requires_score_threshold() -> None:
    weak = FoundationAttack(
        assumption_attacks=("Marker discipline can fail.",),
        invalidation_exploitation=("Partner can omit echo.",),
        vulnerability_strike="False agreement.",
        foundation_score=64,
        attack_summary="Foundation is not strong enough yet.",
    )
    strong = FoundationAttack(
        assumption_attacks=("Marker discipline can fail but is detectable.",),
        invalidation_exploitation=("Omitted echo triggers resend.",),
        vulnerability_strike="False agreement is carried as a structural vulnerability.",
        foundation_score=82,
        attack_summary="Foundation can proceed with explicit gates.",
    )

    assert weak.verdict().value == "REFRAME"
    assert strong.verdict().value == "PASS"


def test_status_progression_requires_third_party_before_locked() -> None:
    assert classify_status(92, round_number=2) == Status.PROVISIONAL_LOCK
    assert classify_status(92, round_number=2, third_party_confirmed=True) == Status.LOCKED
    assert classify_status(86, round_number=5) == Status.UNRESOLVED


def test_database_blueprint_is_content_addressed_and_multi_harness() -> None:
    blueprint = build_database_blueprint()
    sql = blueprint["sql"]

    assert blueprint["strategy"] == "content_addressed_event_store"
    assert "cross_harness_participants" in sql
    assert "cross_harness_payload_blobs" in sql
    assert "content_hash text primary key" in sql
    assert blueprint["token_efficiency"]["store_full_payload_once"] is True


def test_scaffold_package_emits_handoff_bundle_without_hot_state_transcript_duplication() -> None:
    package = build_scaffold_package(_session(), payload_id="ABC123")
    paths = {artifact.path for artifact in package.artifacts}

    assert "cross-harness/README.md" in paths
    assert "cross-harness/origin_packet.md" in paths
    assert "cross-harness/partner_response_template.md" in paths
    assert "cross-harness/implementation_handoff.md" in paths
    assert "cross-harness/session_state.json" in paths
    assert "cross-harness/schema.sql" in paths
    assert "cross-harness/harness_profiles.json" in paths
    assert "cross-harness/consensus_hardening_review.md" in paths
    assert package.total_token_estimate > 0

    state = next(artifact for artifact in package.artifacts if artifact.path.endswith("session_state.json"))
    origin = next(artifact for artifact in package.artifacts if artifact.path.endswith("origin_packet.md"))
    profiles = next(artifact for artifact in package.artifacts if artifact.path.endswith("harness_profiles.json"))

    assert "BEGIN_PAYLOAD" not in state.content
    assert "canonical_protocol" in state.content
    assert content_hash(origin.content) in state.content
    assert state.content.encode("ascii").decode("ascii") == state.content
    assert json.loads(profiles.content)["available_harnesses"]

    removed_terms = ("V" + "CL", "T" + "LP", "L" + "TP")
    for artifact in package.artifacts:
        assert ("triang" + "ulat") not in artifact.content.lower()
        for term in removed_terms:
            assert term not in artifact.content


def test_write_scaffold_package_materializes_ascii_artifacts(tmp_path: Path) -> None:
    package = build_scaffold_package(_session(), payload_id="ABC123")

    written = write_scaffold_package(package, tmp_path)

    assert len(written) == 8
    assert (tmp_path / "cross-harness" / "origin_packet.md").exists()
    for path in written:
        assert tmp_path.resolve() in path.resolve().parents
        path.read_text(encoding="ascii")


def test_write_scaffold_package_blocks_path_escape(tmp_path: Path) -> None:
    package = build_scaffold_package(_session(), payload_id="ABC123")
    bad = type(package)(
        artifacts=(
            *package.artifacts,
            type(package.artifacts[0])("../escape.txt", "bad path", "nope"),
        )
    )

    try:
        write_scaffold_package(bad, tmp_path)
    except ValueError as exc:
        assert "escapes root" in str(exc)
    else:
        raise AssertionError("expected path escape to fail")
