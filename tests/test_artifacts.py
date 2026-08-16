from __future__ import annotations

import base64
import hashlib
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.artifacts import TargetsCatalog, verify_target_artifact
from universal_core.contracts import HardwareProfile
from universal_core.errors import TrustError
from universal_core.registry import MetadataState, SignedMetadata, TrustRoot, key_id_from_public_key, verify_and_accept
from universal_core.resolver import resolve_verified_manifests

NOW = datetime(2026, 8, 16, tzinfo=timezone.utc)
FUTURE = datetime(2030, 1, 1, tzinfo=timezone.utc)


def profile() -> HardwareProfile:
    raw = json.loads((ROOT / "testdata/profiles/synthetic-orion-arm64.json").read_text(encoding="utf-8"))
    return HardwareProfile.from_dict(raw)


def key_entry(private: Ed25519PrivateKey) -> tuple[str, dict[str, str]]:
    public = private.public_key()
    key_id = key_id_from_public_key(public)
    raw = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return key_id, {"scheme": "ed25519", "public": base64.b64encode(raw).decode("ascii")}


def signed(role: str, version: int, body: dict, signer_id: str, signer: Ed25519PrivateKey) -> SignedMetadata:
    unsigned = SignedMetadata(role, version, FUTURE, body, ())
    return unsigned.with_signature(signer_id, signer)


def target_bundle(package_id: str, kind: str, component: str, payload: bytes) -> tuple[str, bytes, bytes, dict]:
    profile_id = "uos.profile.synthetic.orion-arm64-v1"
    manifest = {
        "schema_version": 1,
        "package_id": package_id,
        "version": "0.1.0",
        "kind": kind,
        "provides": {"component": component},
        "compatibility": {
            "architectures": ["arm64"],
            "profile_ids": ["*"] if kind == "core" else [profile_id],
            "kernel_abi": "uos-kabi-orion-1" if kind == "device-support" else None,
            "bootstrap_version_range": ">=0.1.0 <0.2.0"
        },
        "payload": {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload), "install_mode": "inactive-slot"},
        "security": {"signer": "ignored-after-target-binding", "signature": "bound-by-targets", "expires": "2030-01-01T00:00:00Z"}
    }
    if manifest["compatibility"]["kernel_abi"] is None:
        del manifest["compatibility"]["kernel_abi"]
    manifest_bytes = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    target_id = f"{package_id}@0.1.0"
    descriptor = {
        "target_id": target_id,
        "package_id": package_id,
        "manifest": {"sha256": hashlib.sha256(manifest_bytes).hexdigest(), "bytes": len(manifest_bytes)},
        "payload": {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}
    }
    return target_id, manifest_bytes, payload, descriptor


class ArtifactBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        root_private = Ed25519PrivateKey.generate()
        targets_private = Ed25519PrivateKey.generate()
        root_id, root_key = key_entry(root_private)
        self.targets_id, targets_key = key_entry(targets_private)
        self.targets_private = targets_private
        root_body = {
            "keys": {root_id: root_key, self.targets_id: targets_key},
            "roles": {
                "root": {"key_ids": [root_id], "threshold": 1},
                "targets": {"key_ids": [self.targets_id], "threshold": 1},
                "bootstrap": {"key_ids": [self.targets_id], "threshold": 1}
            }
        }
        self.root = TrustRoot.from_metadata(signed("root", 1, root_body, root_id, root_private))
        self.core = target_bundle("uos.core.synthetic-arm64", "core", "core", b"synthetic universal core payload")
        self.display = target_bundle("uos.device.orion.display", "device-support", "display-service", b"synthetic display support")
        self.input = target_bundle("uos.device.orion.input", "device-support", "input-service", b"synthetic input support")
        target_metadata = signed("targets", 1, {"targets": [self.core[3], self.display[3], self.input[3]]}, self.targets_id, self.targets_private)
        self.state = verify_and_accept(self.root, target_metadata, "targets", MetadataState.empty(), NOW)
        self.catalog = TargetsCatalog.from_metadata(target_metadata)

    def test_verified_targets_bind_exact_manifest_and_payload_then_resolve(self) -> None:
        artifacts = [
            verify_target_artifact(self.catalog, target_id, manifest, payload)
            for target_id, manifest, payload, _ in (self.core, self.display, self.input)
        ]
        plan = resolve_verified_manifests(profile(), [artifact.manifest for artifact in artifacts])
        self.assertEqual(plan.core.package_id, "uos.core.synthetic-arm64")
        self.assertEqual([item.component for item in plan.device_support], ["display-service", "input-service"])

    def test_tampered_payload_is_rejected_before_manifest_resolution(self) -> None:
        target_id, manifest, payload, _ = self.core
        with self.assertRaisesRegex(TrustError, "payload bytes"):
            verify_target_artifact(self.catalog, target_id, manifest, payload + b"tampered")

    def test_tampered_manifest_is_rejected_before_json_parsing(self) -> None:
        target_id, manifest, payload, _ = self.core
        with self.assertRaisesRegex(TrustError, "manifest bytes"):
            verify_target_artifact(self.catalog, target_id, manifest.replace(b"core", b"xxxx", 1), payload)

    def test_target_descriptor_cannot_bind_different_package_id(self) -> None:
        target_id, manifest, payload, descriptor = self.core
        altered = {**descriptor, "package_id": "uos.core.other"}
        metadata = signed("targets", 2, {"targets": [altered]}, self.targets_id, self.targets_private)
        catalog = TargetsCatalog.from_metadata(metadata)
        with self.assertRaisesRegex(TrustError, "package id mismatch"):
            verify_target_artifact(catalog, target_id, manifest, payload)


if __name__ == "__main__":
    unittest.main()
