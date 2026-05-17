"""Load Cross-Harness sessions from YAML or JSON config files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import (
    CrossHarnessDiagnosis,
    CrossHarnessDossier,
    CrossHarnessLayer,
    CrossHarnessSession,
    FoundationDisclosure,
    get_harness_profile,
)


def load_mapping(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on optional dependency.
            raise RuntimeError("Install the yaml extra to load YAML configs: pip install PyYAML") from exc
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("session config must be a mapping")
    return data


def _tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    raise ValueError(f"expected string or list, got {type(value).__name__}")


def _profile(data: dict[str, Any]):
    return get_harness_profile(str(data["name"]), model=data.get("model"), role=data.get("role"))


def session_from_mapping(data: dict[str, Any]) -> CrossHarnessSession:
    dossier_data = data.get("dossier") or {}
    foundation_data = data.get("foundation") or {}
    diagnostics_data = data.get("diagnostics") or []
    validators_data = data.get("validators") or []

    if not isinstance(dossier_data, dict):
        raise ValueError("dossier must be a mapping")
    if not isinstance(foundation_data, dict):
        raise ValueError("foundation must be a mapping")
    if not isinstance(diagnostics_data, list):
        raise ValueError("diagnostics must be a list")
    if not isinstance(validators_data, list):
        raise ValueError("validators must be a list")

    return CrossHarnessSession(
        title=str(data["title"]),
        origin=_profile(data["origin"]),
        partner=_profile(data["partner"]),
        validators=tuple(_profile(item) for item in validators_data),
        human_bridge=str(data.get("human_bridge", "Human operator")),
        dossier=CrossHarnessDossier(
            core_problem=str(dossier_data.get("core_problem", "UNKNOWN")),
            goal_state=_tuple(dossier_data.get("goal_state")),
            current_state=_tuple(dossier_data.get("current_state")),
            prior_decisions=_tuple(dossier_data.get("prior_decisions")),
            constraints=_tuple(dossier_data.get("constraints")),
            unknowns=_tuple(dossier_data.get("unknowns")),
            scope=_tuple(dossier_data.get("scope")),
            origin_direction=_tuple(dossier_data.get("origin_direction")),
            prior_round_summary=_tuple(dossier_data.get("prior_round_summary")),
            unknowns_carried=_tuple(dossier_data.get("unknowns_carried")),
            foundation_score=dossier_data.get("foundation_score"),
            structural_vulnerabilities=_tuple(dossier_data.get("structural_vulnerabilities")),
        ),
        foundation=FoundationDisclosure(
            weakest_assumptions=_tuple(foundation_data.get("weakest_assumptions")),
            invalidation_conditions=_tuple(foundation_data.get("invalidation_conditions")),
            key_vulnerability=str(foundation_data.get("key_vulnerability", "")),
        ),
        diagnostics=tuple(
            CrossHarnessDiagnosis(
                item=str(item["item"]),
                observed_layer=CrossHarnessLayer(str(item["observed_layer"])),
                constraint_layer=CrossHarnessLayer(str(item["constraint_layer"])),
                diagnosis=str(item["diagnosis"]),
            )
            for item in diagnostics_data
        ),
    )


def load_session(path: str | Path) -> CrossHarnessSession:
    return session_from_mapping(load_mapping(path))
