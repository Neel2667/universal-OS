from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.artifacts import TargetDescriptor, VerifiedTargetArtifact
from universal_core.contracts import HardwareProfile, PackageManifest
from universal_core.health import HealthPolicy, HealthReport
from universal_core.install import InstallState
from universal_core.preflight import DeviceConditions, PreflightPolicy
from universal_core.services import UniversalSystemServices, UpdateBlockedError

NOW = datetime(2026, 8, 16, tzinfo=timezone.utc)


def profile() -> HardwareProfile:
    return HardwareProfile.from_dict(json.loads((ROOT / "testdata/profiles/synthetic-orion-arm64.json").read_text(encoding="utf-8")))


def artifact(package_id: str, kind: str, component: str, payload: bytes) -> VerifiedTargetArtifact:
    raw = {
        "schema_version": 1,
        "package_id": package_id,
        "version": "0.1.0",
        "kind": kind,
        "provides": {"component": component},
        "compatibility": {
            "architectures": ["arm64"],
            "profile_ids": ["*"] if kind == "core" else ["uos.profile.synthetic.orion-arm64-v1"],
            "bootstrap_version_range": ">=0.1.0 <0.2.0",
        },
        "payload": {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload), "install_mode": "inactive-slot"},
        "security": {"signer": "targets-bound", "signature": "targets-bound", "expires": "2030-01-01T00:00:00Z"},
    }
    if kind == "device-support":
        raw["compatibility"]["kernel_abi"] = "uos-kabi-orion-1"
    manifest = PackageManifest.from_dict(raw)
    target = TargetDescriptor(
        f"{package_id}@0.1.0",
        package_id,
        "0" * 64,
        1,
        hashlib.sha256(payload).hexdigest(),
        len(payload),
    )
    return VerifiedTargetArtifact(target, manifest, payload)


def artifacts() -> tuple[VerifiedTargetArtifact, ...]:
    return (
        artifact("uos.core.synthetic", "core", "core", b"core"),
        artifact("uos.device.orion.display", "device-support", "display-service", b"display"),
        artifact("uos.device.orion.input", "device-support", "input-service", b"input"),
    )


class SystemServiceTests(unittest.TestCase):
    def make_service(self, root: Path) -> UniversalSystemServices:
        return UniversalSystemServices(
            profile(),
            active_target="a",
            journal_directory=root / "journal",
            staging_directory=root / "staging",
            health_policy=HealthPolicy(frozenset({"system-manager", "storage", "ui-shell"}), maximum_age_seconds=60),
            preflight_policy=PreflightPolicy(reserve_bytes=8),
        )

    def safe_conditions(self) -> DeviceConditions:
        return DeviceConditions(80, False, 1024 * 1024, True)

    def test_generic_services_stage_and_commit_verified_update(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory))
            staged = service.stage_verified_update(artifacts(), self.safe_conditions())
            self.assertEqual(staged.journal.state, InstallState.STAGED)
            self.assertEqual(staged.journal.staged_target, "b")
            self.assertEqual(len(staged.staged_artifacts), 3)
            pending = service.request_first_boot()
            report = HealthReport(
                service.profile.profile_id,
                pending.staged_target or "",
                NOW,
                {"system-manager": "ready", "storage": "ready", "ui-shell": "ready"},
            )
            committed = service.confirm_first_boot(report, now=NOW)
            self.assertEqual(committed.state, InstallState.COMMITTED)
            self.assertEqual(committed.active_target, "b")
            self.assertEqual(service.status().active_target, "b")

    def test_failed_health_rolls_back_and_redacted_report_has_no_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory))
            service.stage_verified_update(artifacts(), self.safe_conditions())
            pending = service.request_first_boot()
            report = HealthReport(service.profile.profile_id, pending.staged_target or "", NOW, {"system-manager": "failed", "storage": "ready", "ui-shell": "ready"})
            journal = service.confirm_first_boot(report, now=NOW)
            self.assertEqual(journal.state, InstallState.ROLLED_BACK)
            exported = service.recovery_report().to_json()
            self.assertNotIn(str(Path(directory)), exported)
            self.assertIn('"state":"rolled-back"', exported)

    def test_service_blocks_unsafe_preflight_before_creating_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory))
            with self.assertRaisesRegex(UpdateBlockedError, "battery-below-safe-threshold"):
                service.stage_verified_update(artifacts(), DeviceConditions(10, False, 1024 * 1024, True))
            self.assertEqual(service.status().update_state, "idle")

    def test_restarted_service_reads_pending_transaction_and_can_recover(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            first = self.make_service(path)
            first.stage_verified_update(artifacts(), self.safe_conditions())
            restarted = self.make_service(path)
            self.assertEqual(restarted.status().update_state, "staged")
            rolled_back = restarted.recover("operator-requested")
            self.assertEqual(rolled_back.state, InstallState.ROLLED_BACK)
            self.assertEqual(rolled_back.active_target, "a")


if __name__ == "__main__":
    unittest.main()
