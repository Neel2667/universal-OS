from __future__ import annotations

import base64
import sys
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.errors import TrustError
from universal_core.registry import (
    MetadataState,
    SignedMetadata,
    TrustRoot,
    canonical_json,
    key_id_from_public_key,
    rotate_root,
    verify_and_accept,
    verify_metadata,
)

NOW = datetime(2026, 8, 16, tzinfo=timezone.utc)
FUTURE = datetime(2030, 1, 1, tzinfo=timezone.utc)
PAST = datetime(2025, 1, 1, tzinfo=timezone.utc)


def public_entry(private_key: Ed25519PrivateKey) -> tuple[str, dict[str, str]]:
    public_key = private_key.public_key()
    key_id = key_id_from_public_key(public_key)
    raw = public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return key_id, {"scheme": "ed25519", "public": base64.b64encode(raw).decode("ascii")}


def unsigned(role: str, version: int, signed: dict, expires: datetime = FUTURE) -> SignedMetadata:
    return SignedMetadata(role=role, version=version, expires=expires, signed=signed, signatures=())


def signed(metadata: SignedMetadata, signers: list[tuple[str, Ed25519PrivateKey]]) -> SignedMetadata:
    for key_id, private_key in signers:
        metadata = metadata.with_signature(key_id, private_key)
    return metadata


def make_root(
    key_entries: dict[str, dict[str, str]],
    roles: dict[str, dict[str, object]],
    root_signers: list[tuple[str, Ed25519PrivateKey]],
    *,
    version: int = 1,
    expires: datetime = FUTURE,
) -> TrustRoot:
    root_metadata = signed(unsigned("root", version, {"keys": key_entries, "roles": roles}, expires), root_signers)
    return TrustRoot.from_metadata(root_metadata)


class RegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root_private = Ed25519PrivateKey.generate()
        self.targets_private = Ed25519PrivateKey.generate()
        self.root_id, root_entry = public_entry(self.root_private)
        self.targets_id, targets_entry = public_entry(self.targets_private)
        self.keys = {self.root_id: root_entry, self.targets_id: targets_entry}
        self.roles = {
            "root": {"key_ids": [self.root_id], "threshold": 1},
            "targets": {"key_ids": [self.targets_id], "threshold": 1},
            "bootstrap": {"key_ids": [self.targets_id], "threshold": 1},
        }
        self.root = make_root(self.keys, self.roles, [(self.root_id, self.root_private)])

    def test_ed25519_targets_metadata_verifies_and_advances_state(self) -> None:
        metadata = signed(unsigned("targets", 1, {"packages": ["synthetic-core"]}), [(self.targets_id, self.targets_private)])
        state = verify_and_accept(self.root, metadata, "targets", MetadataState.empty(), NOW)
        self.assertEqual(state.versions, {"targets": 1})

    def test_tampered_canonical_payload_fails_signature_verification(self) -> None:
        metadata = signed(unsigned("targets", 1, {"packages": ["synthetic-core"]}), [(self.targets_id, self.targets_private)])
        tampered = replace(metadata, signed={"packages": ["tampered"]})
        with self.assertRaisesRegex(TrustError, "signature threshold"):
            verify_metadata(self.root, tampered, "targets", NOW)

    def test_threshold_requires_distinct_valid_signers(self) -> None:
        second_private = Ed25519PrivateKey.generate()
        second_id, second_entry = public_entry(second_private)
        keys = {**self.keys, second_id: second_entry}
        roles = {
            **self.roles,
            "targets": {"key_ids": [self.targets_id, second_id], "threshold": 2},
        }
        root = make_root(keys, roles, [(self.root_id, self.root_private)])
        metadata = unsigned("targets", 1, {"packages": []})
        one_signature = signed(metadata, [(self.targets_id, self.targets_private)])
        with self.assertRaisesRegex(TrustError, "threshold 2"):
            verify_metadata(root, one_signature, "targets", NOW)
        two_signatures = signed(metadata, [(self.targets_id, self.targets_private), (second_id, second_private)])
        verify_metadata(root, two_signatures, "targets", NOW)

    def test_expired_metadata_is_rejected_before_acceptance(self) -> None:
        metadata = signed(unsigned("targets", 1, {"packages": []}, PAST), [(self.targets_id, self.targets_private)])
        with self.assertRaisesRegex(TrustError, "expired"):
            verify_metadata(self.root, metadata, "targets", NOW)

    def test_metadata_rollback_is_rejected(self) -> None:
        v2 = signed(unsigned("targets", 2, {"packages": ["v2"]}), [(self.targets_id, self.targets_private)])
        state = verify_and_accept(self.root, v2, "targets", MetadataState.empty(), NOW)
        v1 = signed(unsigned("targets", 1, {"packages": ["v1"]}), [(self.targets_id, self.targets_private)])
        with self.assertRaisesRegex(TrustError, "rollback"):
            verify_and_accept(self.root, v1, "targets", state, NOW)

    def test_root_rotation_requires_old_and_new_root_thresholds(self) -> None:
        new_private = Ed25519PrivateKey.generate()
        new_id, new_entry = public_entry(new_private)
        candidate_roles = {
            "root": {"key_ids": [new_id], "threshold": 1},
            "targets": {"key_ids": [self.targets_id], "threshold": 1},
            "bootstrap": {"key_ids": [self.targets_id], "threshold": 1},
        }
        candidate_unsigned = unsigned("root", 2, {"keys": {new_id: new_entry, self.targets_id: self.keys[self.targets_id]}, "roles": candidate_roles})
        candidate = signed(candidate_unsigned, [(self.root_id, self.root_private), (new_id, new_private)])
        rotated = rotate_root(self.root, candidate, NOW)
        self.assertEqual(rotated.version, 2)
        self.assertIn(new_id, rotated.roles["root"].key_ids)

    def test_root_rotation_rejects_candidate_without_old_root_signature(self) -> None:
        new_private = Ed25519PrivateKey.generate()
        new_id, new_entry = public_entry(new_private)
        roles = {
            "root": {"key_ids": [new_id], "threshold": 1},
            "targets": {"key_ids": [self.targets_id], "threshold": 1},
            "bootstrap": {"key_ids": [self.targets_id], "threshold": 1},
        }
        candidate = signed(
            unsigned("root", 2, {"keys": {new_id: new_entry, self.targets_id: self.keys[self.targets_id]}, "roles": roles}),
            [(new_id, new_private)],
        )
        with self.assertRaisesRegex(TrustError, "threshold"):
            rotate_root(self.root, candidate, NOW)

    def test_canonical_json_has_stable_key_order(self) -> None:
        self.assertEqual(canonical_json({"z": 1, "a": {"b": 2}}), b'{"a":{"b":2},"z":1}')


if __name__ == "__main__":
    unittest.main()
