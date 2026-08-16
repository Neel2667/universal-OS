from __future__ import annotations

import base64
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.discovery import DiscoveryRecord
from universal_core.errors import ResolutionError
from universal_core.bootstrap import select_catalog_bootstrap, verify_and_load_bootstrap_catalog
from universal_core.registry import MetadataState, SignedMetadata, TrustRoot, key_id_from_public_key

NOW = datetime(2026, 8, 16, tzinfo=timezone.utc)
FUTURE = datetime(2030, 1, 1, tzinfo=timezone.utc)


def public_entry(private: Ed25519PrivateKey) -> tuple[str, dict[str, str]]:
    public = private.public_key()
    key_id = key_id_from_public_key(public)
    raw = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return key_id, {"scheme": "ed25519", "public": base64.b64encode(raw).decode("ascii")}


def capsule(version: str = "0.1.0") -> dict:
    return {
        "schema_version": 1,
        "capsule_id": "uos.bootstrap.synthetic-orion",
        "version": version,
        "compatibility": {"architectures": ["arm64"], "board_families": ["synthetic-orion"], "soc_families": ["synthetic-q1"], "partition_models": ["ab"], "transports": ["fastboot"]},
        "payload": {"sha256": "a" * 64, "bytes": 1024, "install_mode": "bootstrap-capsule"},
        "recovery": {"offline_recovery": True, "log_export": True},
        "security": {"signer": "catalog-bound", "signature": "catalog-bound", "expires": "2030-01-01T00:00:00Z"},
    }


def record() -> DiscoveryRecord:
    return DiscoveryRecord.from_dict({"schema_version": 1, "record_id": "uos.discovery.signed-bootstrap-test", "architecture": "arm64", "hardware": {"board_family": "synthetic-orion", "soc_family": "synthetic-q1"}, "boot": {"bootloader_state": "unlocked", "partition_model": "ab"}, "transport": {"protocol": "fastboot"}})


def root_and_catalog(capsules: list[dict]) -> tuple[TrustRoot, SignedMetadata]:
    root_private = Ed25519PrivateKey.generate()
    bootstrap_private = Ed25519PrivateKey.generate()
    root_id, root_key = public_entry(root_private)
    bootstrap_id, bootstrap_key = public_entry(bootstrap_private)
    root_metadata = SignedMetadata("root", 1, FUTURE, {"keys": {root_id: root_key, bootstrap_id: bootstrap_key}, "roles": {"root": {"key_ids": [root_id], "threshold": 1}, "bootstrap": {"key_ids": [bootstrap_id], "threshold": 1}}}, ()).with_signature(root_id, root_private)
    metadata = SignedMetadata("bootstrap", 1, FUTURE, {"capsules": capsules}, ()).with_signature(bootstrap_id, bootstrap_private)
    return TrustRoot.from_metadata(root_metadata), metadata


class SignedBootstrapCatalogTests(unittest.TestCase):
    def test_verified_catalog_selects_newest_compatible_capsule(self) -> None:
        root, metadata = root_and_catalog([capsule("0.1.0"), capsule("0.1.1")])
        catalog, state = verify_and_load_bootstrap_catalog(root, metadata, MetadataState.empty(), now=NOW)
        plan = select_catalog_bootstrap(record(), catalog)
        self.assertEqual(plan.capsule.version, "0.1.1")
        self.assertEqual(state.versions, {"bootstrap": 1})

    def test_catalog_rejects_mismatched_or_ambiguous_capsules(self) -> None:
        bad = capsule()
        bad["compatibility"]["board_families"] = ["different-board"]
        root, metadata = root_and_catalog([bad])
        catalog, _ = verify_and_load_bootstrap_catalog(root, metadata, MetadataState.empty(), now=NOW)
        with self.assertRaises(ResolutionError):
            select_catalog_bootstrap(record(), catalog)
        first = capsule("0.1.1")
        second = {**capsule("0.1.1"), "capsule_id": "uos.bootstrap.synthetic-orion-alt"}
        root, metadata = root_and_catalog([first, second])
        catalog, _ = verify_and_load_bootstrap_catalog(root, metadata, MetadataState.empty(), now=NOW)
        with self.assertRaisesRegex(ResolutionError, "ambiguous"):
            select_catalog_bootstrap(record(), catalog)


if __name__ == "__main__":
    unittest.main()
