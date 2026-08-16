"""Generate and verify a non-production signed UniversalOS test repository.

This module is deliberately located under tools, not the trusted core. It writes
fresh Ed25519 *test-only* private keys only when the caller supplies explicit
acknowledgement. Generated keys must never be used for a release, committed to
Git, uploaded to CI, or treated as a production trust root.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT / "core"))

from universal_core.artifacts import TargetsCatalog, verify_target_artifact  # noqa: E402
from universal_core.registry import MetadataState, SignedMetadata, TrustRoot, key_id_from_public_key, verify_and_accept  # noqa: E402

TEST_EXPIRY = datetime(2030, 1, 1, tzinfo=timezone.utc)


class TestRepositoryError(RuntimeError):
    """The intentionally non-production test repository cannot be created/verified."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _write(path: Path, content: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_bytes(content)
    os.chmod(path, mode)


def _public_entry(private: Ed25519PrivateKey) -> tuple[str, dict[str, str]]:
    public = private.public_key()
    key_id = key_id_from_public_key(public)
    raw = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return key_id, {"scheme": "ed25519", "public": base64.b64encode(raw).decode("ascii")}


def _private_bytes(private: Ed25519PrivateKey) -> bytes:
    return private.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())


def _signed(role: str, version: int, body: dict[str, Any], signer_id: str, signer: Ed25519PrivateKey) -> SignedMetadata:
    return SignedMetadata(role, version, TEST_EXPIRY, body, ()).with_signature(signer_id, signer)


def _package(target_id: str, package_id: str, kind: str, component: str, payload: bytes, profile_id: str) -> tuple[dict[str, Any], bytes, dict[str, Any]]:
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "package_id": package_id,
        "version": "0.1.0",
        "kind": kind,
        "provides": {"component": component},
        "compatibility": {
            "architectures": ["arm64"],
            "profile_ids": ["*"] if kind == "core" else [profile_id],
            "bootstrap_version_range": ">=0.1.0 <0.2.0",
        },
        "payload": {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "install_mode": "inactive-slot",
        },
        "security": {"signer": "test-targets-bound", "signature": "test-targets-bound", "expires": "2030-01-01T00:00:00Z"},
    }
    if kind == "device-support":
        manifest["compatibility"]["kernel_abi"] = "uos-kabi-test-1"
    manifest_bytes = _canonical_json(manifest)
    descriptor = {
        "target_id": target_id,
        "package_id": package_id,
        "manifest": {"sha256": hashlib.sha256(manifest_bytes).hexdigest(), "bytes": len(manifest_bytes)},
        "payload": {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)},
    }
    return manifest, manifest_bytes, descriptor


@dataclass(frozen=True)
class TestRepositoryReport:
    path: Path
    target_count: int
    root_key_id: str
    targets_key_id: str


def generate_test_repository(destination: Path, *, acknowledge_test_keys: bool) -> TestRepositoryReport:
    """Create a self-contained, harmless test repository with test-only keys."""
    if not acknowledge_test_keys:
        raise TestRepositoryError("refusing to generate private test keys without explicit acknowledgement")
    destination = destination.resolve()
    if destination == ROOT or ROOT in destination.parents:
        raise TestRepositoryError("test repository destination must be outside the source checkout")
    if destination.exists() and any(destination.iterdir()):
        raise TestRepositoryError("test repository destination must be empty")
    destination.mkdir(mode=0o700, parents=True, exist_ok=True)

    root_private = Ed25519PrivateKey.generate()
    targets_private = Ed25519PrivateKey.generate()
    root_id, root_entry = _public_entry(root_private)
    targets_id, targets_entry = _public_entry(targets_private)
    root_body = {
        "keys": {root_id: root_entry, targets_id: targets_entry},
        "roles": {
            "root": {"key_ids": [root_id], "threshold": 1},
            "targets": {"key_ids": [targets_id], "threshold": 1},
            "bootstrap": {"key_ids": [targets_id], "threshold": 1},
        },
    }
    root_metadata = _signed("root", 1, root_body, root_id, root_private)

    profile_id = "uos.profile.synthetic.test-arm64-v1"
    inputs = [
        ("uos.core.test-arm64@0.1.0", "uos.core.test-arm64", "core", "core", b"UNIVERSALOS-TEST-CORE-ONLY\n"),
        ("uos.device.test.display@0.1.0", "uos.device.test.display", "device-support", "display-service", b"UNIVERSALOS-TEST-DISPLAY-ONLY\n"),
        ("uos.device.test.input@0.1.0", "uos.device.test.input", "device-support", "input-service", b"UNIVERSALOS-TEST-INPUT-ONLY\n"),
    ]
    target_descriptors = []
    package_blobs: list[tuple[str, bytes, bytes]] = []
    for target_id, package_id, kind, component, payload in inputs:
        _, manifest_bytes, descriptor = _package(target_id, package_id, kind, component, payload, profile_id)
        target_descriptors.append(descriptor)
        package_blobs.append((target_id, manifest_bytes, payload))
    targets_metadata = _signed("targets", 1, {"targets": target_descriptors}, targets_id, targets_private)

    _write(destination / "TEST_ONLY_NOT_FOR_RELEASE.txt", b"This repository and its keys are test-only. Never use them for a release, device, or production trust root.\n")
    _write(destination / "metadata" / "root.json", _canonical_json(root_metadata.to_dict()) + b"\n")
    _write(destination / "metadata" / "targets.json", _canonical_json(targets_metadata.to_dict()) + b"\n")
    _write(destination / "keys" / "test-root-ed25519.raw", _private_bytes(root_private), mode=0o600)
    _write(destination / "keys" / "test-targets-ed25519.raw", _private_bytes(targets_private), mode=0o600)
    for target_id, manifest_bytes, payload in package_blobs:
        _write(destination / "manifests" / f"{target_id}.json", manifest_bytes + b"\n")
        _write(destination / "artifacts" / f"{target_id}.bin", payload)
    return TestRepositoryReport(destination, len(package_blobs), root_id, targets_id)


def verify_test_repository(destination: Path, *, now: datetime) -> TestRepositoryReport:
    """Verify the generated root, targets, and every bound manifest/payload pair."""
    destination = destination.resolve()
    marker = destination / "TEST_ONLY_NOT_FOR_RELEASE.txt"
    if not marker.exists():
        raise TestRepositoryError("refusing to verify a repository without the explicit test-only marker")
    try:
        root_raw = json.loads((destination / "metadata" / "root.json").read_text(encoding="utf-8"))
        targets_raw = json.loads((destination / "metadata" / "targets.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TestRepositoryError("test repository metadata is unreadable") from exc
    root_metadata = SignedMetadata.from_dict(root_raw)
    root = TrustRoot.from_metadata(root_metadata)
    targets_metadata = SignedMetadata.from_dict(targets_raw)
    verify_and_accept(root, targets_metadata, "targets", MetadataState.empty(), now)
    catalog = TargetsCatalog.from_metadata(targets_metadata)
    for descriptor in catalog.descriptors.values():
        manifest = (destination / "manifests" / f"{descriptor.target_id}.json").read_bytes().rstrip(b"\n")
        payload = (destination / "artifacts" / f"{descriptor.target_id}.bin").read_bytes()
        verify_target_artifact(catalog, descriptor.target_id, manifest, payload)
    role = root.roles["targets"]
    return TestRepositoryReport(destination, len(catalog.descriptors), next(iter(root.roles["root"].key_ids)), next(iter(role.key_ids)))
