"""Pure preflight policy for a future UniversalOS installer.

The caller supplies measured device conditions. This module does not read a
battery, inspect storage, or communicate with hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .contracts import HardwareProfile


@dataclass(frozen=True)
class DeviceConditions:
    battery_percent: int
    external_power: bool
    free_bytes: int
    offline_recovery_available: bool


@dataclass(frozen=True)
class PreflightPolicy:
    minimum_battery_percent: int = 50
    reserve_bytes: int = 256 * 1024 * 1024
    require_offline_recovery: bool = True


@dataclass(frozen=True)
class PreflightResult:
    allowed: bool
    reasons: tuple[str, ...]
    required_bytes: int


def evaluate_preflight(
    profile: HardwareProfile,
    payload_sizes: Iterable[int],
    conditions: DeviceConditions,
    policy: PreflightPolicy = PreflightPolicy(),
) -> PreflightResult:
    """Return every blocking reason; do not permit a partial unsafe install."""
    sizes = tuple(payload_sizes)
    reasons: list[str] = []
    if any(not isinstance(size, int) or size < 0 for size in sizes):
        reasons.append("invalid-payload-size")
    required_bytes = sum(size for size in sizes if isinstance(size, int) and size >= 0) + policy.reserve_bytes
    if profile.partition_model == "single-slot":
        reasons.append("single-slot-normal-install-unsupported")
    if conditions.battery_percent < 0 or conditions.battery_percent > 100:
        reasons.append("invalid-battery-reading")
    elif not conditions.external_power and conditions.battery_percent < policy.minimum_battery_percent:
        reasons.append("battery-below-safe-threshold")
    if conditions.free_bytes < 0:
        reasons.append("invalid-free-space-reading")
    elif conditions.free_bytes < required_bytes:
        reasons.append("insufficient-safe-staging-space")
    if policy.require_offline_recovery and not conditions.offline_recovery_available:
        reasons.append("offline-recovery-unavailable")
    return PreflightResult(not reasons, tuple(reasons), required_bytes)
