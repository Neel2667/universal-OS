from __future__ import annotations

import base64
import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.discovery import DiscoveryRecord
from universal_core.errors import ResolutionError
from universal_core.installer import InstallerPhase, UniversalInstallerRehearsal
from universal_core.profiles import MeasuredHardwareFacts
from universal_core.registry import SignedMetadata, TrustRoot, key_id_from_public_key
from universal_core.transfer import TransferManifest

NOW = datetime(2026, 8, 16, tzinfo=timezone.utc)
FUTURE = datetime(2030, 1, 1, tzinfo=timezone.utc)


def public_entry(private: Ed25519PrivateKey) -> tuple[str, dict[str, str]]:
    public = private.public_key()
    key_id = key_id_from_public_key(public)
    raw = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return key_id, {"scheme": "ed25519", "public": base64.b64encode(raw).decode("ascii")}


def signed(role: str, body: dict, key_id: str, private: Ed25519PrivateKey) -> SignedMetadata:
    return SignedMetadata(role, 1, FUTURE, body, ()).with_signature(key_id, private)


def capsule() -> dict:
    return {
        "schema_version": 1,
        "capsule_id": "uos.bootstrap.synthetic-orion",
        "version": "0.1.0",
        "compatibility": {"architectures": ["arm64"], "board_families": ["synthetic-orion"], "soc_families": ["synthetic-q1"], "partition_models": ["ab"], "transports": ["fastboot"]},
        "payload": {"sha256": "a" * 64, "bytes": 1024, "install_mode": "bootstrap-capsule"},
        "recovery": {"offline_recovery": True, "log_export": True},
        "security": {"signer": "catalog", "signature": "catalog", "expires": "2030-01-01T00:00:00Z"},
    }


def profile() -> dict:
    return json.loads((ROOT / "testdata/profiles/synthetic-orion-arm64.json").read_text(encoding="utf-8"))


def package(target_id: str, package_id: str, kind: str, component: str, payload: bytes) -> tuple[dict, bytes, bytes]:
    manifest = {
        "schema_version": 1,
        "package_id": package_id,
        "version": "0.1.0",
        "kind": kind,
        "provides": {"component": component},
        "compatibility": {"architectures": ["arm64"], "profile_ids": ["*"] if kind == "core" else ["uos.profile.synthetic.orion-arm64-v1"], "bootstrap_version_range": ">=0.1.0 <0.2.0"},
        "payload": {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload), "install_mode": "inactive-slot"},
        "security": {"signer": "targets", "signature": "targets", "expires": "2030-01-01T00:00:00Z"},
    }
    if kind == "device-support":
        manifest["compatibility"]["kernel_abi"] = "uos-kabi-orion-1"
    return manifest, json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8"), payload


def transfer(target_id: str, kind: str, data: bytes, transfer_id: str) -> TransferManifest:
    chunk_bytes = 4096
    chunks = [data[offset : offset + chunk_bytes] for offset in range(0, len(data), chunk_bytes)]
    return TransferManifest.from_dict({"schema_version": 1, "transfer_id": transfer_id, "target_id": target_id, "artifact_kind": kind, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "chunk_bytes": chunk_bytes, "chunk_sha256": [hashlib.sha256(chunk).hexdigest() for chunk in chunks]})


class InstallerRehearsalTests(unittest.TestCase):
    def setup_rehearsal(self, directory: Path) -> tuple[UniversalInstallerRehearsal, SignedMetadata, SignedMetadata, SignedMetadata, list[tuple[str, bytes, bytes]]]:
        root_private, bootstrap_private, profiles_private, targets_private = (Ed25519PrivateKey.generate() for _ in range(4))
        root_id, root_key = public_entry(root_private)
        bootstrap_id, bootstrap_key = public_entry(bootstrap_private)
        profiles_id, profiles_key = public_entry(profiles_private)
        targets_id, targets_key = public_entry(targets_private)
        root = TrustRoot.from_metadata(signed("root", {"keys": {root_id: root_key, bootstrap_id: bootstrap_key, profiles_id: profiles_key, targets_id: targets_key}, "roles": {"root": {"key_ids": [root_id], "threshold": 1}, "bootstrap": {"key_ids": [bootstrap_id], "threshold": 1}, "profiles": {"key_ids": [profiles_id], "threshold": 1}, "targets": {"key_ids": [targets_id], "threshold": 1}}}, root_id, root_private))
        bootstrap_metadata = signed("bootstrap", {"capsules": [capsule()]}, bootstrap_id, bootstrap_private)
        profiles_metadata = signed("profiles", {"profiles": [{"profile": profile(), "match": {"board_families": ["synthetic-orion"], "soc_families": ["synthetic-q1"], "revision_classes": ["a"]}}]}, profiles_id, profiles_private)
        inputs = [
            ("uos.core.rehearsal@0.1.0", "uos.core.rehearsal", "core", "core", b"core"),
            ("uos.display.rehearsal@0.1.0", "uos.display.rehearsal", "device-support", "display-service", b"display"),
            ("uos.input.rehearsal@0.1.0", "uos.input.rehearsal", "device-support", "input-service", b"input"),
        ]
        target_descriptors, blobs = [], []
        for target_id, package_id, kind, component, payload in inputs:
            manifest, manifest_bytes, payload_bytes = package(target_id, package_id, kind, component, payload)
            target_descriptors.append({"target_id": target_id, "package_id": package_id, "manifest": {"sha256": hashlib.sha256(manifest_bytes).hexdigest(), "bytes": len(manifest_bytes)}, "payload": {"sha256": hashlib.sha256(payload_bytes).hexdigest(), "bytes": len(payload_bytes)}})
            blobs.append((target_id, manifest_bytes, payload_bytes))
        targets_metadata = signed("targets", {"targets": target_descriptors}, targets_id, targets_private)
        discovery = DiscoveryRecord.from_dict({"schema_version": 1, "record_id": "uos.discovery.rehearsal", "architecture": "arm64", "hardware": {"board_family": "synthetic-orion", "soc_family": "synthetic-q1"}, "boot": {"bootloader_state": "unlocked", "partition_model": "ab"}, "transport": {"protocol": "fastboot"}})
        facts = MeasuredHardwareFacts.from_dict({"schema_version": 1, "architecture": "arm64", "board_family": "synthetic-orion", "soc_family": "synthetic-q1", "revision_class": "a", "partition_model": "ab", "kernel_abi": "uos-kabi-orion-1"})
        return UniversalInstallerRehearsal(root, discovery, facts, directory, now=NOW), bootstrap_metadata, profiles_metadata, targets_metadata, blobs

    def test_rehearsal_chains_signed_catalogs_and_usb_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session, bootstrap_meta, profiles_meta, targets_meta, blobs = self.setup_rehearsal(Path(directory))
            session.select_bootstrap(bootstrap_meta)
            self.assertEqual(session.status().phase, InstallerPhase.BOOTSTRAP_SELECTED)
            session.select_profile(profiles_meta)
            session.verify_targets(targets_meta)
            for number, (target_id, manifest_bytes, payload) in enumerate(blobs):
                manifest_transfer = transfer(target_id, "manifest", manifest_bytes, f"manifest-{number:03d}")
                payload_transfer = transfer(target_id, "payload", payload, f"payload-{number:03d}")
                session.receive(manifest_transfer, {0: manifest_bytes})
                session.receive(payload_transfer, {0: payload})
            artifacts = session.artifacts()
            self.assertEqual(len(artifacts), 3)
            self.assertEqual(session.status().phase, InstallerPhase.ARTIFACTS_READY)

    def test_rehearsal_rejects_targets_before_bootstrap_and_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session, _, _, targets_meta, _ = self.setup_rehearsal(Path(directory))
            with self.assertRaises(ResolutionError):
                session.verify_targets(targets_meta)


if __name__ == "__main__":
    unittest.main()
