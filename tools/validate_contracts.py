#!/usr/bin/env python3
"""Validate portable UniversalOS contract fixtures and print safe resolution plans.

This is a host-side development tool. It does not connect to a phone, use a
network, download packages, verify real cryptographic signatures, or write any
boot/update artifact.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.bootstrap import BootstrapCapsule, select_bootstrap  # noqa: E402
from universal_core.contracts import HardwareProfile, PackageManifest  # noqa: E402
from universal_core.discovery import DiscoveryRecord  # noqa: E402
from universal_core.resolver import resolve  # noqa: E402
from universal_core.trust import FixtureTrustVerifier  # noqa: E402

FIXTURE_TIME = datetime(2026, 8, 16, tzinfo=timezone.utc)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def main() -> int:
    records = [DiscoveryRecord.from_dict(load_json(path)) for path in sorted((ROOT / "testdata/discovery").glob("*.json"))]
    capsules = [BootstrapCapsule.from_dict(load_json(path)) for path in sorted((ROOT / "testdata/bootstrap_capsules").glob("*.json"))]
    profiles = [HardwareProfile.from_dict(load_json(path)) for path in sorted((ROOT / "testdata/profiles").glob("*.json"))]
    manifests = [PackageManifest.from_dict(load_json(path)) for path in sorted((ROOT / "testdata/packages").glob("*.json"))]
    verifier = FixtureTrustVerifier({"fixture-root"})

    for record in records:
        plan = select_bootstrap(record, capsules, verifier, now=FIXTURE_TIME)
        print(f"{record.record_id}: bootstrap={plan.capsule.capsule_id}@{plan.capsule.version}; rejected={len(plan.rejections)}")
    for profile in profiles:
        plan = resolve(profile, manifests, verifier, now=FIXTURE_TIME)
        support = ", ".join(item.component for item in plan.device_support)
        print(f"{profile.profile_id}: core={plan.core.package_id}@{plan.core.version}; support=[{support}]; rejected={len(plan.rejections)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
