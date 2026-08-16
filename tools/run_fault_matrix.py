#!/usr/bin/env python3
"""Run deterministic non-device fault scenarios against the install journal model."""
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
from universal_core.contracts import HardwareProfile
from universal_core.install import InstallJournal, InstallState

def profile() -> HardwareProfile:
    return HardwareProfile.from_dict(json.loads((ROOT / "testdata/profiles/synthetic-orion-arm64.json").read_text()))

def run() -> dict[str, str]:
    base = InstallJournal.begin(profile(), "a").metadata_verified().artifacts_verified(["uos.core"])
    outcomes = {
        "interrupted-after-artifact-verification": base.interrupted("simulated-power-loss").state.value,
        "interrupted-after-staging": base.stage().interrupted("simulated-power-loss").state.value,
        "interrupted-on-first-boot": base.stage().request_first_boot().interrupted("simulated-power-loss").state.value,
        "failed-health": base.stage().request_first_boot().confirm_health(False).state.value,
        "healthy-first-boot": base.stage().request_first_boot().confirm_health(True).state.value,
    }
    if any(value != InstallState.ROLLED_BACK.value for key, value in outcomes.items() if key != "healthy-first-boot"):
        raise RuntimeError("fault scenario did not roll back")
    if outcomes["healthy-first-boot"] != InstallState.COMMITTED.value:
        raise RuntimeError("healthy scenario did not commit")
    return outcomes
if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
