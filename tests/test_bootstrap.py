from __future__ import annotations

import json
import sys
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.bootstrap import BootstrapCapsule, select_bootstrap
from universal_core.discovery import DiscoveryRecord
from universal_core.errors import ContractError, ResolutionError
from universal_core.trust import FixtureTrustVerifier

NOW = datetime(2026, 8, 16, tzinfo=timezone.utc)
VERIFIER = FixtureTrustVerifier({"fixture-root"})


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def records() -> dict[str, DiscoveryRecord]:
    return {path.stem: DiscoveryRecord.from_dict(load(path)) for path in (ROOT / "testdata/discovery").glob("*.json")}


def capsules() -> list[BootstrapCapsule]:
    return [BootstrapCapsule.from_dict(load(path)) for path in (ROOT / "testdata/bootstrap_capsules").glob("*.json")]


class BootstrapTests(unittest.TestCase):
    def test_orion_selects_newest_exact_trusted_capsule(self) -> None:
        plan = select_bootstrap(records()["synthetic-orion-unlocked"], capsules(), VERIFIER, now=NOW)
        self.assertEqual(plan.capsule.capsule_id, "uos.bootstrap.synthetic-orion")
        self.assertEqual(plan.capsule.version, "0.1.1")
        reasons = {item.capsule_id: item.reason for item in plan.rejections}
        self.assertEqual(reasons["uos.bootstrap.synthetic-wrong-board"], "board family mismatch")
        self.assertTrue(reasons["uos.bootstrap.synthetic-rogue"].startswith("trust rejected:"))

    def test_cedar_selects_its_own_transport_and_architecture_capsule(self) -> None:
        plan = select_bootstrap(records()["synthetic-cedar-unlocked"], capsules(), VERIFIER, now=NOW)
        self.assertEqual(plan.capsule.capsule_id, "uos.bootstrap.synthetic-cedar")
        self.assertEqual(plan.capsule.transports, frozenset({"recovery"}))

    def test_locked_bootloader_fails_before_any_capsule_selection(self) -> None:
        record = replace(records()["synthetic-orion-unlocked"], bootloader_state="locked")
        with self.assertRaisesRegex(ResolutionError, "not confirmed unlocked"):
            select_bootstrap(record, capsules(), VERIFIER, now=NOW)

    def test_ambiguous_newest_capsules_fail_closed(self) -> None:
        record = records()["synthetic-orion-unlocked"]
        original = next(item for item in capsules() if item.capsule_id == "uos.bootstrap.synthetic-orion" and item.version == "0.1.1")
        ambiguous = replace(original, capsule_id="uos.bootstrap.synthetic-orion-alt")
        with self.assertRaisesRegex(ResolutionError, "ambiguous newest"):
            select_bootstrap(record, [original, ambiguous], VERIFIER, now=NOW)

    def test_wildcard_board_capsule_is_rejected_by_contract(self) -> None:
        raw = load(ROOT / "testdata/bootstrap_capsules/orion-v010.json")
        raw["compatibility"]["board_families"] = ["*"]
        with self.assertRaises(ContractError):
            BootstrapCapsule.from_dict(raw)

    def test_discovery_record_rejects_personal_identifier_field(self) -> None:
        raw = load(ROOT / "testdata/discovery/synthetic-orion-unlocked.json")
        raw["serial_number"] = "must-not-be-accepted"
        with self.assertRaises(ContractError):
            DiscoveryRecord.from_dict(raw)


if __name__ == "__main__":
    unittest.main()
