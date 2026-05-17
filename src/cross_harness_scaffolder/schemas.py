"""JSON schema exports for generated packets, state, and session configs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SESSION_CONFIG_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "CrossHarnessSessionConfig",
    "type": "object",
    "required": ["title", "origin", "partner", "dossier", "foundation", "diagnostics"],
    "properties": {
        "title": {"type": "string"},
        "human_bridge": {"type": "string"},
        "origin": {"$ref": "#/$defs/profile"},
        "partner": {"$ref": "#/$defs/profile"},
        "validators": {"type": "array", "items": {"$ref": "#/$defs/profile"}},
        "dossier": {
            "type": "object",
            "required": ["core_problem", "goal_state", "current_state", "constraints", "scope"],
            "properties": {
                "core_problem": {"type": "string"},
                "goal_state": {"type": "array", "items": {"type": "string"}},
                "current_state": {"type": "array", "items": {"type": "string"}},
                "constraints": {"type": "array", "items": {"type": "string"}},
                "scope": {"type": "array", "items": {"type": "string"}},
                "origin_direction": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": True,
        },
        "foundation": {
            "type": "object",
            "required": ["weakest_assumptions", "invalidation_conditions", "key_vulnerability"],
            "properties": {
                "weakest_assumptions": {"type": "array", "minItems": 1, "maxItems": 3, "items": {"type": "string"}},
                "invalidation_conditions": {"type": "array", "minItems": 1, "maxItems": 2, "items": {"type": "string"}},
                "key_vulnerability": {"type": "string"},
            },
        },
        "diagnostics": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["item", "observed_layer", "constraint_layer", "diagnosis"],
                "properties": {
                    "item": {"type": "string"},
                    "observed_layer": {"type": "string"},
                    "constraint_layer": {"type": "string"},
                    "diagnosis": {"type": "string"},
                },
            },
        },
    },
    "$defs": {
        "profile": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "model": {"type": "string"},
                "role": {"type": "string"},
            },
        }
    },
}

PACKET_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "CrossHarnessPacket",
    "type": "object",
    "required": ["core_problem_statement", "partner_harness_packet", "transmission_checklist"],
    "properties": {
        "core_problem_statement": {"type": "string"},
        "partner_harness_packet": {"type": "string", "pattern": "BEGIN_PAYLOAD"},
        "transmission_checklist": {"type": "array", "items": {"type": "string"}},
    },
}

STATE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "CrossHarnessCompactState",
    "type": "object",
    "required": ["protocol_version", "canonical_protocol", "participants", "origin_packet_hash"],
    "properties": {
        "protocol_version": {"type": "string"},
        "canonical_protocol": {"type": "object"},
        "title": {"type": "string"},
        "phase": {"type": "integer"},
        "round_number": {"type": "integer"},
        "status": {"type": "string"},
        "participants": {"type": "array"},
        "dossier_hash": {"type": "string"},
        "origin_packet_hash": {"type": "string"},
        "partner_template_hash": {"type": "string"},
        "diagnostic_items": {"type": "array", "items": {"type": "string"}},
        "token_budget": {"type": "object"},
    },
}


def schema_bundle() -> dict[str, dict[str, Any]]:
    return {
        "session_config.schema.json": SESSION_CONFIG_SCHEMA,
        "packet.schema.json": PACKET_SCHEMA,
        "state.schema.json": STATE_SCHEMA,
    }


def export_json_schemas(root: str | Path) -> tuple[Path, ...]:
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for filename, schema in schema_bundle().items():
        target = root_path / filename
        target.write_text(json.dumps(schema, indent=2, sort_keys=True), encoding="ascii")
        written.append(target)
    return tuple(written)
