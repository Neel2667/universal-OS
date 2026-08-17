from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.contracts import HardwareProfile, PackageManifest
from universal_core.errors import ContractError, ResolutionError
from universal_core.resolver import resolve
from universal_core.trust import FixtureTrustVerifier

NOW = datetime(2026, 8, 16, tzinfo=timezone.utc)
VERIFIER = FixtureTrustVerifier({"fixture-root"})


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def profiles() -> dict[str, HardwareProfile]:
    return {path.stem: HardwareProfile.from_dict(load(path)) for path in (ROOT / "testdata/profiles").glob("*.json")}


def packages() -> list[PackageManifest]:
    return [PackageManifest.from_dict(load(path)) for path in (ROOT / "testdata/packages").glob("*.json")]


class ContractTests(unittest.TestCase):
    def test_synthetic_profiles_are_non_personal_and_parse(self) -> None:
        loaded = profiles()
        self.assertEqual(set(loaded), {"synthetic-orion-arm64", "synthetic-cedar-armv7"})
        self.assertEqual(loaded["synthetic-orion-arm64"].architecture, "arm64")
        self.assertEqual(loaded["synthetic-cedar-armv7"].architecture, "armv7")
        self.assertNotIn("serial", loaded["synthetic-orion-arm64"].__dict__)

    def test_profile_rejects_unknown_field(self) -> None:
        raw = load(ROOT / "testdata/profiles/synthetic-orion-arm64.json")
        raw["imei"] = "must-not-be-accepted"
        with self.assertRaises(ContractError):
            HardwareProfile.from_dict(raw)

    def test_arm64_resolution_does_not_choose_armv7_or_rogue_core(self) -> None:
        profile = profiles()["synthetic-orion-arm64"]
        plan = resolve(profile, packages(), VERIFIER, now=NOW)
        self.assertEqual(plan.core.package_id, "uos.core.arm64")
        self.assertEqual([item.component for item in plan.device_support], ["display-service", "input-service"])
        reasons = {item.package_id: item.reason for item in plan.rejections}
        self.assertEqual(reasons["uos.core.armv7"], "architecture mismatch")
        self.assertTrue(reasons["uos.core.rogue"].startswith("trust rejected:"))

    def test_armv7_resolution_selects_different_core_and_support(self) -> None:
        profile = profiles()["synthetic-cedar-armv7"]
        plan = resolve(profile, packages(), VERIFIER, now=NOW)
        self.assertEqual(plan.core.package_id, "uos.core.armv7")
        self.assertEqual([item.package_id for item in plan.device_support], ["uos.device.cedar.display", "uos.device.cedar.input"])

    def test_missing_required_support_is_a_hard_failure(self) -> None:
        profile = profiles()["synthetic-orion-arm64"]
        manifests = [item for item in packages() if item.package_id != "uos.device.orion.input"]
        with self.assertRaisesRegex(ResolutionError, "input-service"):
            resolve(profile, manifests, VERIFIER, now=NOW)

    def test_invalid_digest_is_rejected_before_resolution(self) -> None:
        raw = load(ROOT / "testdata/packages/core-arm64-v010.json")
        raw["payload"]["sha256"] = "short"
        with self.assertRaises(ContractError):
            PackageManifest.from_dict(raw)


if __name__ == "__main__":
    unittest.main()
