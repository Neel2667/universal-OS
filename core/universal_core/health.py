"""Local post-boot health contract for the installation state machine.

This is a policy/validation contract only. It does not attest real services;
platform-specific implementation must later authenticate reports and bind them
to verified boot state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from .errors import ContractError

HEALTH_STATES = frozenset({"ready", "failed", "unknown"})


@dataclass(frozen=True)
class HealthReport:
    profile_id: str
    boot_target: str
    generated_at: datetime
    services: Mapping[str, str]

    def __post_init__(self) -> None:
        if not self.profile_id or not self.boot_target:
            raise ContractError("health report requires profile and boot target")
        if self.generated_at.tzinfo is None:
            raise ContractError("health report timestamp must include a timezone")
        if not self.services:
            raise ContractError("health report must contain at least one critical service")
        for name, state in self.services.items():
            if not name or state not in HEALTH_STATES:
                raise ContractError("health report contains an invalid service state")


@dataclass(frozen=True)
class HealthPolicy:
    required_services: frozenset[str]
    maximum_age_seconds: int = 180

    def __post_init__(self) -> None:
        if not self.required_services:
            raise ContractError("health policy requires at least one critical service")
        if self.maximum_age_seconds < 1:
            raise ContractError("health policy maximum age must be positive")


def health_is_confirmed(
    report: HealthReport,
    policy: HealthPolicy,
    *,
    expected_profile_id: str,
    expected_boot_target: str,
    now: datetime,
) -> bool:
    """Return true only for fresh, matching, locally complete health evidence."""
    if now.tzinfo is None:
        raise ContractError("health verification time must include a timezone")
    if report.profile_id != expected_profile_id or report.boot_target != expected_boot_target:
        return False
    age = (now.astimezone(timezone.utc) - report.generated_at.astimezone(timezone.utc)).total_seconds()
    if age < 0 or age > policy.maximum_age_seconds:
        return False
    return all(report.services.get(service) == "ready" for service in policy.required_services)
