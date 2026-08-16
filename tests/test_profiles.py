from __future__ import annotations

import base64
import json
import sys
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.errors import ContractError, ResolutionError
from universal_core.profiles import MeasuredHardwareFacts, ProfileCatalog, verify_and_load_profiles
from universal_core.registry import MetadataState, SignedMetadata, TrustRoot, key_id_from_public_key

NOW = datetime(2026, 8, 16, tzinfo=timezone.utc)
FUTURE = datetime(2030, 1, 1, tzinfo=timezone.utc)


def public_entry(private: Ed25519PrivateKey) -> tuple[str, dict[str, str]]:
    public = private.public_key()
    key_id = key_id_from_public_key(public)
    raw = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return key_id, {"scheme": "ed25519", "public": base64.b64encode(raw).decode("ascii")}


def profile_raw() -> dict:
    return json.loads((ROOT / "testdata/profiles/synthetic-orion-arm64.json").read_text(encoding="utf-8"))


def root_and_profiles_metadata(entries: list[dict]) -> tuple[TrustRoot, SignedMetadata]:
    root_private = Ed25519PrivateKey.generate()
    profiles_private = Ed25519PrivateKey.generate()
    root_id, root_key = public_entry(root_private)
    profiles_id, profiles_key = public_entry(profiles_private)
    root_body = {
        "keys": {root_id: root_key, profiles_id: profiles_key},
        "roles": {
            "root": {"key_ids": [root_id], "threshold": 1},
            "profiles": {"key_ids": [profiles_id], "threshold": 1},
        },
    }
    root_metadata = SignedMetadata("root", 1, FUTURE, root_body, ()).with_signature(root_id, root_private)
    profiles_metadata = SignedMetadata("profiles", 1, FUTURE, {"profiles": entries}, ()).with_signature(profiles_id, profiles_private)
    return TrustRoot.from_metadata(root_metadata), profiles_metadata


def facts() -> MeasuredHardwareFacts:
    return MeasuredHardwareFacts.from_dict(
        {
            "schema_version": 1,
            "architecture": "arm64",
            "board_family": "synthetic-orion",
            "soc_family": "synthetic-q1",
            "revision_class": "a",
            "partition_model": "ab",
            "kernel_abi": "uos-kabi-orion-1",
        }
    )


class ProfilesTests(unittest.TestCase):
    def entry(self) -> dict:
        return {
            "profile": profile_raw(),
            "match": {"board_families": ["synthetic-orion"], "soc_families": ["synthetic-q1"], "revision_classes": ["a", "b"]},
        }

    def test_signed_catalog_selects_exact_local_profile(self) -> None:
        root, metadata = root_and_profiles_metadata([self.entry()])
        catalog, state = verify_and_load_profiles(root, metadata, MetadataState.empty(), now=NOW)
        selected = catalog.select(facts())
        self.assertEqual(selected.profile_id, "uos.profile.synthetic.orion-arm64-v1")
        self.assertEqual(state.versions, {"profiles": 1})

    def test_unknown_board_or_abi_fails_closed(self) -> None:
        root, metadata = root_and_profiles_metadata([self.entry()])
        catalog, _ = verify_and_load_profiles(root, metadata, MetadataState.empty(), now=NOW)
        with self.assertRaises(ResolutionError):
            catalog.select(replace(facts(), board_family="unknown-board"))
        with self.assertRaises(ResolutionError):
            catalog.select(replace(facts(), kernel_abi="wrong-abi"))

    def test_ambiguous_profile_match_is_rejected(self) -> None:
        duplicate = self.entry()
        duplicate["profile"] = {**profile_raw(), "profile_id": "uos.profile.synthetic.orion-duplicate-v1"}
        root, metadata = root_and_profiles_metadata([self.entry(), duplicate])
        catalog, _ = verify_and_load_profiles(root, metadata, MetadataState.empty(), now=NOW)
        with self.assertRaisesRegex(ResolutionError, "ambiguous"):
            catalog.select(facts())

    def test_personal_or_unknown_measured_field_is_rejected(self) -> None:
        raw = {
            "schema_version": 1,
            "architecture": "arm64",
            "board_family": "synthetic-orion",
            "soc_family": "synthetic-q1",
            "revision_class": "a",
            "partition_model": "ab",
            "kernel_abi": "uos-kabi-orion-1",
            "imei": "must-not-be-accepted",
        }
        with self.assertRaises(ContractError):
            MeasuredHardwareFacts.from_dict(raw)


if __name__ == "__main__":
    unittest.main()
