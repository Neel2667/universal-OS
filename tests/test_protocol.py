from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.contracts import HardwareProfile
from universal_core.health import HealthPolicy
from universal_core.install import InstallJournal, InstallState
from universal_core.protocol import CallerContext, LocalServiceGateway, ServiceRequest
from universal_core.services import UniversalSystemServices

NOW = datetime(2026, 8, 16, tzinfo=timezone.utc)


def profile() -> HardwareProfile:
    return HardwareProfile.from_dict(json.loads((ROOT / "testdata/profiles/synthetic-orion-arm64.json").read_text(encoding="utf-8")))


def request(request_id: str, service: str, method: str, params: dict | None = None) -> ServiceRequest:
    return ServiceRequest.from_dict({"schema_version": 1, "request_id": request_id, "service": service, "method": method, "params": params or {}})


class ProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.services = UniversalSystemServices(
            profile(),
            active_target="a",
            journal_directory=root / "journal",
            staging_directory=root / "staging",
            health_policy=HealthPolicy(frozenset({"system-manager", "storage"}), maximum_age_seconds=60),
        )
        self.gateway = LocalServiceGateway(self.services)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def stage_journal(self) -> None:
        journal = (
            InstallJournal.begin(self.services.profile, "a")
            .metadata_verified()
            .artifacts_verified(["uos.core"])
            .stage()
        )
        self.services.journal_store.save(journal)

    def test_profile_read_is_allowed_but_update_read_needs_separate_capability(self) -> None:
        app = CallerContext("sample-app", frozenset({"uos.device.read"}))
        status = self.gateway.dispatch(app, request("one", "device", "get-status"), now=NOW)
        self.assertTrue(status.ok)
        self.assertEqual(status.result["profile_id"], "uos.profile.synthetic.orion-arm64-v1")
        denied = self.gateway.dispatch(app, request("two", "update", "get-status"), now=NOW)
        self.assertFalse(denied.ok)
        self.assertEqual(denied.error_code, "service.permission-denied")

    def test_unprivileged_ui_cannot_report_health(self) -> None:
        self.stage_journal()
        self.gateway.dispatch(CallerContext("system-updater", frozenset({"uos.update.request-first-boot"})), request("boot", "update", "request-first-boot"), now=NOW)
        ui = CallerContext("system-ui", frozenset({"uos.update.read"}))
        denied = self.gateway.dispatch(
            ui,
            request(
                "health-ui",
                "health",
                "report",
                {"profile_id": self.services.profile.profile_id, "boot_target": "b", "generated_at": "2026-08-16T00:00:00Z", "services": {"system-manager": "ready", "storage": "ready"}},
            ),
            now=NOW,
        )
        self.assertFalse(denied.ok)
        self.assertEqual(denied.error_code, "service.permission-denied")

    def test_authenticated_health_service_can_commit_matching_report(self) -> None:
        self.stage_journal()
        updater = CallerContext("system-updater", frozenset({"uos.update.request-first-boot"}))
        pending = self.gateway.dispatch(updater, request("boot", "update", "request-first-boot"), now=NOW)
        self.assertTrue(pending.ok)
        health = CallerContext("verified-health-service", frozenset({"uos.health.report"}))
        confirmed = self.gateway.dispatch(
            health,
            request(
                "health",
                "health",
                "report",
                {"profile_id": self.services.profile.profile_id, "boot_target": "b", "generated_at": "2026-08-16T00:00:00Z", "services": {"system-manager": "ready", "storage": "ready"}},
            ),
            now=NOW,
        )
        self.assertTrue(confirmed.ok)
        self.assertEqual(confirmed.result["update_state"], InstallState.COMMITTED.value)
        self.assertEqual(confirmed.result["active_target"], "b")

    def test_recovery_response_is_redacted(self) -> None:
        self.stage_journal()
        recovery = CallerContext("recovery-ui", frozenset({"uos.recovery.read"}))
        response = self.gateway.dispatch(recovery, request("report", "recovery", "get-report"), now=NOW)
        self.assertTrue(response.ok)
        rendered = json.dumps(response.to_dict())
        self.assertNotIn(self.directory.name, rendered)
        self.assertEqual(response.result["state"], "staged")

    def test_invalid_envelope_is_rejected_before_dispatch(self) -> None:
        with self.assertRaises(Exception):
            ServiceRequest.from_dict({"schema_version": 1, "request_id": "x", "service": "device", "method": "get-status"})


if __name__ == "__main__":
    unittest.main()
