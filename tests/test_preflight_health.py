from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.contracts import HardwareProfile
from universal_core.health import HealthPolicy, HealthReport, health_is_confirmed
from universal_core.preflight import DeviceConditions, PreflightPolicy, evaluate_preflight

NOW = datetime(2026, 8, 16, tzinfo=timezone.utc)


def profile(name: str) -> HardwareProfile:
    return HardwareProfile.from_dict(json.loads((ROOT / f"testdata/profiles/{name}.json").read_text(encoding="utf-8")))


class PreflightAndHealthTests(unittest.TestCase):
    def test_preflight_allows_safe_ab_profile(self) -> None:
        result = evaluate_preflight(
            profile("synthetic-orion-arm64"),
            [100, 200],
            DeviceConditions(battery_percent=80, external_power=False, free_bytes=1024 * 1024 * 1024, offline_recovery_available=True),
            PreflightPolicy(reserve_bytes=1024),
        )
        self.assertTrue(result.allowed)
        self.assertEqual(result.reasons, ())

    def test_preflight_collects_all_blocking_reasons(self) -> None:
        result = evaluate_preflight(
            profile("synthetic-orion-arm64"),
            [500],
            DeviceConditions(battery_percent=10, external_power=False, free_bytes=100, offline_recovery_available=False),
            PreflightPolicy(minimum_battery_percent=50, reserve_bytes=1024),
        )
        self.assertFalse(result.allowed)
        self.assertEqual(
            set(result.reasons),
            {"battery-below-safe-threshold", "insufficient-safe-staging-space", "offline-recovery-unavailable"},
        )

    def test_single_slot_profile_is_blocked_by_preflight(self) -> None:
        original = profile("synthetic-orion-arm64")
        # The parser allows the model; preflight is the normal-install safety gate.
        single_slot = HardwareProfile(
            original.profile_id,
            original.display_name,
            original.support_tier,
            original.architecture,
            original.board_family,
            original.soc_family,
            original.bootstrap_version,
            original.kernel_abi,
            "single-slot",
            original.verified_boot,
            original.rollback_protection,
            original.capabilities,
            original.required_components,
        )
        result = evaluate_preflight(
            single_slot,
            [],
            DeviceConditions(100, True, 1024 * 1024 * 1024, True),
            PreflightPolicy(reserve_bytes=0),
        )
        self.assertIn("single-slot-normal-install-unsupported", result.reasons)

    def test_health_requires_fresh_matching_ready_services(self) -> None:
        report = HealthReport(
            "uos.profile.synthetic.orion-arm64-v1",
            "b",
            NOW - timedelta(seconds=10),
            {"system-manager": "ready", "storage": "ready", "ui-shell": "ready"},
        )
        policy = HealthPolicy(frozenset({"system-manager", "storage", "ui-shell"}), maximum_age_seconds=60)
        self.assertTrue(health_is_confirmed(report, policy, expected_profile_id=report.profile_id, expected_boot_target="b", now=NOW))
        self.assertFalse(health_is_confirmed(report, policy, expected_profile_id=report.profile_id, expected_boot_target="a", now=NOW))

    def test_stale_or_failed_health_does_not_confirm(self) -> None:
        policy = HealthPolicy(frozenset({"system-manager"}), maximum_age_seconds=30)
        stale = HealthReport("profile", "b", NOW - timedelta(seconds=31), {"system-manager": "ready"})
        failed = HealthReport("profile", "b", NOW, {"system-manager": "failed"})
        self.assertFalse(health_is_confirmed(stale, policy, expected_profile_id="profile", expected_boot_target="b", now=NOW))
        self.assertFalse(health_is_confirmed(failed, policy, expected_profile_id="profile", expected_boot_target="b", now=NOW))


if __name__ == "__main__":
    unittest.main()
