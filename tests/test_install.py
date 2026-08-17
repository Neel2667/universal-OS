from __future__ import annotations

import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.contracts import HardwareProfile
from universal_core.errors import ResolutionError
from universal_core.install import InstallJournal, InstallState


def load_profile(name: str) -> HardwareProfile:
    raw = json.loads((ROOT / f"testdata/profiles/{name}.json").read_text(encoding="utf-8"))
    return HardwareProfile.from_dict(raw)


class InstallJournalTests(unittest.TestCase):
    def test_ab_install_commits_only_after_healthy_first_boot(self) -> None:
        journal = InstallJournal.begin(load_profile("synthetic-orion-arm64"), "a")
        committed = (
            journal.metadata_verified()
            .artifacts_verified(["uos.core", "uos.display", "uos.input"])
            .stage()
            .request_first_boot()
            .confirm_health(True)
        )
        self.assertEqual(committed.state, InstallState.COMMITTED)
        self.assertEqual(committed.active_target, "b")
        self.assertIsNone(committed.staged_target)

    def test_failed_health_preserves_known_good_ab_target(self) -> None:
        journal = (
            InstallJournal.begin(load_profile("synthetic-orion-arm64"), "a")
            .metadata_verified()
            .artifacts_verified(["uos.core"])
            .stage()
            .request_first_boot()
            .confirm_health(False)
        )
        self.assertEqual(journal.state, InstallState.ROLLED_BACK)
        self.assertEqual(journal.active_target, "a")
        self.assertIn("rolled-back:health-check-failed", journal.events)

    def test_interruption_after_staging_rolls_back_to_known_good_target(self) -> None:
        journal = (
            InstallJournal.begin(load_profile("synthetic-orion-arm64"), "b")
            .metadata_verified()
            .artifacts_verified(["uos.core"])
            .stage()
            .interrupted("power-loss")
        )
        self.assertEqual(journal.state, InstallState.ROLLED_BACK)
        self.assertEqual(journal.active_target, "b")

    def test_transactional_profile_uses_next_generation(self) -> None:
        journal = (
            InstallJournal.begin(load_profile("synthetic-cedar-armv7"), "transaction:4")
            .metadata_verified()
            .artifacts_verified(["uos.core"])
            .stage()
        )
        self.assertEqual(journal.staged_target, "transaction:5")

    def test_single_slot_normal_full_system_installation_is_rejected(self) -> None:
        profile = replace(load_profile("synthetic-orion-arm64"), partition_model="single-slot")
        journal = InstallJournal.begin(profile, "system").metadata_verified().artifacts_verified(["uos.core"])
        with self.assertRaisesRegex(ResolutionError, "single-slot"):
            journal.stage()


if __name__ == "__main__":
    unittest.main()
