"""Session config validation for CLI and CI use."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .core import CrossHarnessLayer, get_harness_profile
from .schemas import SESSION_CONFIG_SCHEMA
from .session_config import load_mapping, session_from_mapping


@dataclass(frozen=True)
class ConfigValidationIssue:
    path: str
    message: str
    severity: str = "error"


@dataclass(frozen=True)
class ConfigValidationResult:
    issues: tuple[ConfigValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "issues": [
                {"path": issue.path, "message": issue.message, "severity": issue.severity}
                for issue in self.issues
            ],
        }

    def render_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def render_markdown(self) -> str:
        lines = ["# Cross-Harness Config Validation", "", f"Status: {'PASS' if self.ok else 'FAIL'}", ""]
        if not self.issues:
            lines.append("- PASS | config | info | session config is valid")
            return "\n".join(lines)
        for issue in self.issues:
            status = "FAIL" if issue.severity == "error" else "WARN"
            lines.append(f"- {status} | {issue.path} | {issue.severity} | {issue.message}")
        return "\n".join(lines)


def validate_session_config(
    path: str | Path,
    *,
    use_json_schema: bool = False,
    schema_path: str | Path | None = None,
) -> ConfigValidationResult:
    return validate_session_config_mapping(
        load_mapping(path),
        use_json_schema=use_json_schema or schema_path is not None,
        schema_path=schema_path,
    )


def validate_session_config_mapping(
    data: dict[str, Any],
    *,
    use_json_schema: bool = False,
    schema_path: str | Path | None = None,
) -> ConfigValidationResult:
    issues: list[ConfigValidationIssue] = []

    def add(path: str, message: str, severity: str = "error") -> None:
        issues.append(ConfigValidationIssue(path=path, message=message, severity=severity))

    def require_mapping(path: str, value: Any) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            add(path, "must be a mapping")
            return None
        return value

    def require_list(path: str, value: Any, *, min_items: int = 0, max_items: int | None = None) -> list[Any] | None:
        if not isinstance(value, list):
            add(path, "must be a list")
            return None
        if len(value) < min_items:
            add(path, f"must include at least {min_items} item(s)")
        if max_items is not None and len(value) > max_items:
            add(path, f"must include no more than {max_items} item(s)")
        return value

    for key in ("title", "origin", "partner", "dossier", "foundation", "diagnostics"):
        if key not in data:
            add(key, "is required")

    if use_json_schema:
        issues.extend(validate_mapping_against_json_schema(data, schema_path=schema_path))

    if "title" in data and not isinstance(data["title"], str):
        add("title", "must be a string")

    for key in ("origin", "partner"):
        profile = require_mapping(key, data.get(key))
        if profile is not None:
            _validate_profile(profile, key, add)

    validators = data.get("validators", [])
    if validators is not None:
        validator_list = require_list("validators", validators)
        if validator_list is not None:
            for idx, profile in enumerate(validator_list):
                profile_map = require_mapping(f"validators[{idx}]", profile)
                if profile_map is not None:
                    _validate_profile(profile_map, f"validators[{idx}]", add)

    dossier = require_mapping("dossier", data.get("dossier"))
    if dossier is not None:
        for field in ("core_problem", "goal_state", "current_state", "constraints", "scope"):
            if field not in dossier:
                add(f"dossier.{field}", "is required")
        if "core_problem" in dossier and not isinstance(dossier["core_problem"], str):
            add("dossier.core_problem", "must be a string")
        for field in ("goal_state", "current_state", "constraints", "scope", "origin_direction"):
            if field in dossier:
                require_list(f"dossier.{field}", dossier[field], min_items=1 if field != "origin_direction" else 0)

    foundation = require_mapping("foundation", data.get("foundation"))
    if foundation is not None:
        assumptions = require_list("foundation.weakest_assumptions", foundation.get("weakest_assumptions"), min_items=1, max_items=3)
        invalidations = require_list(
            "foundation.invalidation_conditions",
            foundation.get("invalidation_conditions"),
            min_items=1,
            max_items=2,
        )
        if assumptions is not None:
            _validate_string_items(assumptions, "foundation.weakest_assumptions", add)
        if invalidations is not None:
            _validate_string_items(invalidations, "foundation.invalidation_conditions", add)
        if not isinstance(foundation.get("key_vulnerability"), str) or not foundation.get("key_vulnerability"):
            add("foundation.key_vulnerability", "must be a non-empty string")

    diagnostics = require_list("diagnostics", data.get("diagnostics"), min_items=1)
    if diagnostics is not None:
        allowed_layers = {layer.value for layer in CrossHarnessLayer}
        for idx, item in enumerate(diagnostics):
            item_map = require_mapping(f"diagnostics[{idx}]", item)
            if item_map is None:
                continue
            for field in ("item", "observed_layer", "constraint_layer", "diagnosis"):
                if field not in item_map:
                    add(f"diagnostics[{idx}].{field}", "is required")
            for field in ("observed_layer", "constraint_layer"):
                if field in item_map and item_map[field] not in allowed_layers:
                    add(f"diagnostics[{idx}].{field}", f"must be one of {sorted(allowed_layers)}")

    if not issues:
        try:
            session = session_from_mapping(data)
        except Exception as exc:
            add("session", f"could not build session: {exc}")
        else:
            for error in session.dossier.validate():
                add("dossier", error)
            if session.foundation is None:
                add("foundation", "foundation disclosure is required")
            else:
                for error in session.foundation.validate():
                    add("foundation", error)

    return ConfigValidationResult(issues=tuple(issues))


def json_schema_validator_available() -> bool:
    try:
        import jsonschema  # type: ignore  # noqa: F401
    except ImportError:
        return False
    return True


def validate_mapping_against_json_schema(
    data: dict[str, Any],
    *,
    schema_path: str | Path | None = None,
) -> tuple[ConfigValidationIssue, ...]:
    try:
        from jsonschema import Draft202012Validator  # type: ignore
    except ImportError:
        return (
            ConfigValidationIssue(
                path="json_schema",
                message="jsonschema is not installed; install the schema extra to enable JSON Schema validation",
                severity="warning",
            ),
        )

    schema = _load_schema(schema_path) if schema_path else SESSION_CONFIG_SCHEMA
    validator = Draft202012Validator(schema)
    issues = []
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in error.path) or "$"
        issues.append(ConfigValidationIssue(path=f"json_schema.{path}", message=error.message, severity="error"))
    return tuple(issues)


def _load_schema(schema_path: str | Path | None) -> dict[str, Any]:
    if schema_path is None:
        return SESSION_CONFIG_SCHEMA
    source = Path(schema_path)
    if source.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on optional dependency.
            raise RuntimeError("Install the yaml extra to load YAML schemas: pip install .[yaml]") from exc
        schema = yaml.safe_load(source.read_text(encoding="utf-8"))
    else:
        schema = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise ValueError("external schema must be a mapping")
    return schema


def _validate_profile(profile: dict[str, Any], path: str, add) -> None:
    name = profile.get("name")
    if not isinstance(name, str) or not name:
        add(f"{path}.name", "must be a non-empty string")
        return
    try:
        get_harness_profile(name, model=profile.get("model"), role=profile.get("role"))
    except KeyError:
        add(f"{path}.name", f"unknown harness profile: {name}")
    for field in ("model", "role"):
        if field in profile and profile[field] is not None and not isinstance(profile[field], str):
            add(f"{path}.{field}", "must be a string")


def _validate_string_items(items: list[Any], path: str, add) -> None:
    for idx, item in enumerate(items):
        if not isinstance(item, str) or not item:
            add(f"{path}[{idx}]", "must be a non-empty string")
