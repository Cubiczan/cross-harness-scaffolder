"""Signed bundle manifests for release-gate audit trails."""
from __future__ import annotations

import hashlib
import hmac
import json
from base64 import b64decode, b64encode
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .core import ScaffoldArtifact, ScaffoldPackage, content_hash, estimate_tokens


MANIFEST_PATH = "cross-harness/bundle_manifest.json"
MANIFEST_VERSION = "chs-bundle-manifest-v1"
SIGNATURE_ALGORITHM = "hmac_sha256"
PUBLIC_KEY_SIGNATURE_ALGORITHM = "ed25519"
TRANSPARENCY_LOG_VERSION = "chs-transparency-log-v1"


def build_bundle_manifest(
    package: ScaffoldPackage,
    *,
    created_at: str | None = None,
    signer: str = "cross-harness-scaffolder",
) -> dict[str, Any]:
    return build_artifact_manifest(package.artifacts, created_at=created_at, signer=signer)


def build_artifact_manifest(
    artifacts: Iterable[ScaffoldArtifact],
    *,
    created_at: str | None = None,
    signer: str = "cross-harness-scaffolder",
) -> dict[str, Any]:
    entries = [
        artifact.manifest_entry()
        for artifact in artifacts
        if artifact.path.replace("\\", "/") != MANIFEST_PATH
    ]
    entries.sort(key=lambda item: item["path"])
    return _manifest_from_entries(entries, created_at=created_at, signer=signer)


def build_directory_manifest(
    root: str | Path,
    *,
    created_at: str | None = None,
    signer: str = "cross-harness-scaffolder",
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    entries: list[dict[str, Any]] = []
    for path in sorted(item for item in root_path.rglob("*") if item.is_file()):
        rel = path.relative_to(root_path).as_posix()
        if rel == "bundle_manifest.json" or rel.endswith("/bundle_manifest.json"):
            continue
        data = path.read_bytes()
        try:
            token_estimate = estimate_tokens(data.decode("utf-8"))
        except UnicodeDecodeError:
            token_estimate = max(1, len(data) // 4)
        entries.append(
            {
                "path": rel,
                "purpose": "bundle file",
                "content_hash": hashlib.sha256(data).hexdigest(),
                "token_estimate": token_estimate,
            }
        )
    return _manifest_from_entries(entries, created_at=created_at, signer=signer)


def sign_bundle_manifest(
    manifest: dict[str, Any],
    secret: str,
    *,
    key_id: str,
) -> dict[str, Any]:
    if not secret:
        raise ValueError("signing secret is required")
    signed = dict(manifest)
    signature = hmac.new(secret.encode("utf-8"), _canonical_json(signed).encode("ascii"), hashlib.sha256).hexdigest()
    signed["signature"] = {
        "algorithm": SIGNATURE_ALGORITHM,
        "key_id": key_id,
        "value": signature,
    }
    return signed


def sign_bundle_manifest_public_key(
    manifest: dict[str, Any],
    private_key_pem: str | bytes,
    *,
    key_id: str,
    password: str | bytes | None = None,
) -> dict[str, Any]:
    """Sign a manifest with an Ed25519 private key when cryptography is installed."""

    serialization, ed25519 = _cryptography_modules()
    key_bytes = private_key_pem.encode("utf-8") if isinstance(private_key_pem, str) else private_key_pem
    password_bytes = password.encode("utf-8") if isinstance(password, str) else password
    private_key = serialization.load_pem_private_key(key_bytes, password=password_bytes)
    if not isinstance(private_key, ed25519.Ed25519PrivateKey):
        raise ValueError("private key must be an Ed25519 PEM key")
    signed = dict(manifest)
    signature = private_key.sign(_canonical_json(signed).encode("ascii"))
    signed["signature"] = {
        "algorithm": PUBLIC_KEY_SIGNATURE_ALGORITHM,
        "key_id": key_id,
        "value": b64encode(signature).decode("ascii"),
    }
    return signed


def verify_bundle_manifest_signature(manifest: dict[str, Any], secret: str) -> bool:
    signature = manifest.get("signature")
    if not isinstance(signature, dict):
        return False
    value = signature.get("value")
    if not isinstance(value, str):
        return False
    unsigned = dict(manifest)
    unsigned.pop("signature", None)
    expected = hmac.new(secret.encode("utf-8"), _canonical_json(unsigned).encode("ascii"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(value, expected)


def verify_bundle_manifest_public_key(manifest: dict[str, Any], public_key_pem: str | bytes) -> bool:
    serialization, ed25519 = _cryptography_modules()
    signature = manifest.get("signature")
    if not isinstance(signature, dict):
        return False
    if signature.get("algorithm") != PUBLIC_KEY_SIGNATURE_ALGORITHM:
        return False
    value = signature.get("value")
    if not isinstance(value, str):
        return False
    key_bytes = public_key_pem.encode("utf-8") if isinstance(public_key_pem, str) else public_key_pem
    public_key = serialization.load_pem_public_key(key_bytes)
    if not isinstance(public_key, ed25519.Ed25519PublicKey):
        raise ValueError("public key must be an Ed25519 PEM key")
    unsigned = dict(manifest)
    unsigned.pop("signature", None)
    try:
        public_key.verify(b64decode(value.encode("ascii")), _canonical_json(unsigned).encode("ascii"))
    except Exception:
        return False
    return True


def attach_bundle_manifest(package: ScaffoldPackage, *, signer: str = "cross-harness-scaffolder") -> ScaffoldPackage:
    manifest = build_bundle_manifest(package, signer=signer)
    return _replace_manifest(package, manifest)


def sign_scaffold_package(
    package: ScaffoldPackage,
    secret: str,
    *,
    key_id: str,
    signer: str = "cross-harness-scaffolder",
) -> ScaffoldPackage:
    manifest = sign_bundle_manifest(build_bundle_manifest(package, signer=signer), secret, key_id=key_id)
    return _replace_manifest(package, manifest)


def sign_scaffold_package_public_key(
    package: ScaffoldPackage,
    private_key_pem: str | bytes,
    *,
    key_id: str,
    signer: str = "cross-harness-scaffolder",
    password: str | bytes | None = None,
) -> ScaffoldPackage:
    manifest = sign_bundle_manifest_public_key(
        build_bundle_manifest(package, signer=signer),
        private_key_pem,
        key_id=key_id,
        password=password,
    )
    return _replace_manifest(package, manifest)


def write_signed_directory_manifest(
    root: str | Path,
    output: str | Path,
    secret: str,
    *,
    key_id: str,
    signer: str = "cross-harness-scaffolder",
) -> Path:
    manifest = sign_bundle_manifest(build_directory_manifest(root, signer=signer), secret, key_id=key_id)
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="ascii")
    return target


def write_public_key_signed_directory_manifest(
    root: str | Path,
    output: str | Path,
    private_key_pem: str | bytes,
    *,
    key_id: str,
    signer: str = "cross-harness-scaffolder",
    password: str | bytes | None = None,
) -> Path:
    manifest = sign_bundle_manifest_public_key(
        build_directory_manifest(root, signer=signer),
        private_key_pem,
        key_id=key_id,
        password=password,
    )
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="ascii")
    return target


def build_transparency_log_entry(
    manifest: dict[str, Any],
    *,
    log_id: str = "local",
    source: str = "",
    previous_entry_hash: str | None = None,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    manifest_hash = hashlib.sha256(_canonical_json(manifest).encode("ascii")).hexdigest()
    signature = manifest.get("signature") if isinstance(manifest.get("signature"), dict) else {}
    entry = {
        "log_version": TRANSPARENCY_LOG_VERSION,
        "log_id": log_id,
        "recorded_at": recorded_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": source,
        "manifest_hash": manifest_hash,
        "manifest_version": manifest.get("manifest_version", ""),
        "manifest_created_at": manifest.get("created_at", ""),
        "signer": manifest.get("signer", ""),
        "artifact_count": manifest.get("artifact_count", 0),
        "signature_algorithm": signature.get("algorithm", ""),
        "signature_key_id": signature.get("key_id", ""),
        "signature_value": signature.get("value", ""),
        "previous_entry_hash": previous_entry_hash or "",
    }
    entry["entry_hash"] = hashlib.sha256(_canonical_json(entry).encode("ascii")).hexdigest()
    return entry


def export_transparency_log(
    manifests: Iterable[dict[str, Any]],
    output: str | Path,
    *,
    log_id: str = "local",
    sources: Iterable[str] | None = None,
    append: bool = False,
    chain: bool = True,
) -> Path:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    source_list = list(sources or ())
    entries = []
    previous = _last_log_entry_hash(target) if append and chain else None
    for idx, manifest in enumerate(manifests):
        source = source_list[idx] if idx < len(source_list) else ""
        entry = build_transparency_log_entry(
            manifest,
            log_id=log_id,
            source=source,
            previous_entry_hash=previous if chain else None,
        )
        previous = entry["entry_hash"]
        entries.append(entry)
    mode = "a" if append else "w"
    with target.open(mode, encoding="ascii") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=True, sort_keys=True) + "\n")
    return target


def export_transparency_log_from_paths(
    manifest_paths: Iterable[str | Path],
    output: str | Path,
    *,
    log_id: str = "local",
    append: bool = False,
    chain: bool = True,
) -> Path:
    paths = [Path(path) for path in manifest_paths]
    manifests = [json.loads(path.read_text(encoding="ascii")) for path in paths]
    return export_transparency_log(
        manifests,
        output,
        log_id=log_id,
        sources=[path.as_posix() for path in paths],
        append=append,
        chain=chain,
    )


def _replace_manifest(package: ScaffoldPackage, manifest: dict[str, Any]) -> ScaffoldPackage:
    content = json.dumps(manifest, indent=2, sort_keys=True)
    manifest_artifact = ScaffoldArtifact(MANIFEST_PATH, "release-gate audit manifest", content)
    artifacts = tuple(
        artifact
        for artifact in package.artifacts
        if artifact.path.replace("\\", "/") != MANIFEST_PATH
    )
    return replace(package, artifacts=(*artifacts, manifest_artifact))


def _manifest_from_entries(
    entries: list[dict[str, Any]],
    *,
    created_at: str | None,
    signer: str,
) -> dict[str, Any]:
    entries.sort(key=lambda item: item["path"])
    return {
        "manifest_version": MANIFEST_VERSION,
        "created_at": created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "signer": signer,
        "artifact_count": len(entries),
        "total_token_estimate": sum(int(item["token_estimate"]) for item in entries),
        "artifacts": entries,
    }


def _canonical_json(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("signature", None)
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _last_log_entry_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    last = ""
    for line in path.read_text(encoding="ascii").splitlines():
        if line.strip():
            last = line
    if not last:
        return None
    try:
        entry = json.loads(last)
    except json.JSONDecodeError:
        return None
    value = entry.get("entry_hash")
    return value if isinstance(value, str) and value else None


def _cryptography_modules():
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
    except ImportError as exc:  # pragma: no cover - depends on optional extra.
        raise RuntimeError("Install the crypto extra for Ed25519 signing: pip install .[crypto]") from exc
    return serialization, ed25519
