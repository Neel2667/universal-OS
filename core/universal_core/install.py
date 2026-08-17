"""Pure, append-only installation state machine for UniversalOS planning.

This module models safe staging/first-boot/rollback behavior. It performs no
filesystem, partition, network, subprocess, USB, or bootloader operation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .contracts import HardwareProfile
from .errors import ResolutionError


class InstallState(str, Enum):
    IDLE = "idle"
    METADATA_VERIFIED = "metadata-verified"
    ARTIFACTS_VERIFIED = "artifacts-verified"
    STAGED = "staged"
    PENDING_FIRST_BOOT = "pending-first-boot"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled-back"


@dataclass(frozen=True)
class InstallJournal:
    """State/evidence record for one simulated installation transaction."""

    profile_id: str
    partition_model: str
    active_target: str
    state: InstallState
    staged_target: str | None
    package_ids: tuple[str, ...]
    events: tuple[str, ...]

    @classmethod
    def begin(cls, profile: HardwareProfile, active_target: str) -> "InstallJournal":
        if profile.partition_model == "ab" and active_target not in {"a", "b"}:
            raise ResolutionError("A/B installation requires active target 'a' or 'b'")
        if profile.partition_model == "transactional" and not active_target.startswith("transaction:"):
            raise ResolutionError("transactional installation requires a transaction:<generation> active target")
        if profile.partition_model == "single-slot" and active_target != "system":
            raise ResolutionError("single-slot installation requires active target 'system'")
        return cls(profile.profile_id, profile.partition_model, active_target, InstallState.IDLE, None, (), ("journal-created",))

    def _transition(self, expected: InstallState, next_state: InstallState, event: str, **changes: object) -> "InstallJournal":
        if self.state != expected:
            raise ResolutionError(f"invalid install transition: {self.state.value} → {next_state.value}")
        values = {
            "profile_id": self.profile_id,
            "partition_model": self.partition_model,
            "active_target": self.active_target,
            "state": next_state,
            "staged_target": self.staged_target,
            "package_ids": self.package_ids,
            "events": (*self.events, event),
        }
        values.update(changes)
        return InstallJournal(**values)  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, object]:
        """Serialize only non-sensitive transaction state for JournalStore."""
        return {
            "profile_id": self.profile_id,
            "partition_model": self.partition_model,
            "active_target": self.active_target,
            "state": self.state.value,
            "staged_target": self.staged_target,
            "package_ids": list(self.package_ids),
            "events": list(self.events),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "InstallJournal":
        expected = {"profile_id", "partition_model", "active_target", "state", "staged_target", "package_ids", "events"}
        if set(raw) != expected:
            raise ResolutionError("serialized install journal has unknown or missing fields")
        try:
            state = InstallState(raw["state"])
        except (TypeError, ValueError) as exc:
            raise ResolutionError("serialized install journal has invalid state") from exc
        package_ids = raw["package_ids"]
        events = raw["events"]
        if not isinstance(package_ids, list) or not all(isinstance(item, str) and item for item in package_ids):
            raise ResolutionError("serialized install journal has invalid package ids")
        if not isinstance(events, list) or not all(isinstance(item, str) and item for item in events):
            raise ResolutionError("serialized install journal has invalid events")
        profile_id = raw["profile_id"]
        partition_model = raw["partition_model"]
        active_target = raw["active_target"]
        staged_target = raw["staged_target"]
        if not all(isinstance(item, str) and item for item in (profile_id, partition_model, active_target)):
            raise ResolutionError("serialized install journal has invalid identity fields")
        if staged_target is not None and (not isinstance(staged_target, str) or not staged_target):
            raise ResolutionError("serialized install journal has invalid staged target")
        return cls(profile_id, partition_model, active_target, state, staged_target, tuple(package_ids), tuple(events))

    def metadata_verified(self) -> "InstallJournal":
        return self._transition(InstallState.IDLE, InstallState.METADATA_VERIFIED, "metadata-verified")

    def artifacts_verified(self, package_ids: Iterable[str]) -> "InstallJournal":
        packages = tuple(sorted(set(package_ids)))
        if not packages:
            raise ResolutionError("installation requires at least one verified package")
        return self._transition(
            InstallState.METADATA_VERIFIED,
            InstallState.ARTIFACTS_VERIFIED,
            "artifacts-verified",
            package_ids=packages,
        )

    def stage(self) -> "InstallJournal":
        if self.partition_model == "single-slot":
            raise ResolutionError("single-slot profiles cannot use normal atomic full-system installation")
        if self.partition_model == "ab":
            target = "b" if self.active_target == "a" else "a"
        else:
            current_generation = int(self.active_target.split(":", 1)[1])
            target = f"transaction:{current_generation + 1}"
        return self._transition(InstallState.ARTIFACTS_VERIFIED, InstallState.STAGED, f"staged:{target}", staged_target=target)

    def request_first_boot(self) -> "InstallJournal":
        if self.staged_target is None:
            raise ResolutionError("cannot request first boot without a staged target")
        return self._transition(InstallState.STAGED, InstallState.PENDING_FIRST_BOOT, f"first-boot-requested:{self.staged_target}")

    def confirm_health(self, healthy: bool) -> "InstallJournal":
        if not healthy:
            return self.rollback("health-check-failed")
        if self.staged_target is None:
            raise ResolutionError("cannot commit without a staged target")
        return self._transition(
            InstallState.PENDING_FIRST_BOOT,
            InstallState.COMMITTED,
            f"health-confirmed:{self.staged_target}",
            active_target=self.staged_target,
            staged_target=None,
        )

    def rollback(self, reason: str) -> "InstallJournal":
        if self.state not in {InstallState.ARTIFACTS_VERIFIED, InstallState.STAGED, InstallState.PENDING_FIRST_BOOT}:
            raise ResolutionError(f"cannot roll back from state {self.state.value}")
        return InstallJournal(
            self.profile_id,
            self.partition_model,
            self.active_target,
            InstallState.ROLLED_BACK,
            None,
            self.package_ids,
            (*self.events, f"rolled-back:{reason}"),
        )

    def interrupted(self, phase: str) -> "InstallJournal":
        """Model power/process loss before commit; known-good active target is preserved."""
        if self.state in {InstallState.COMMITTED, InstallState.ROLLED_BACK}:
            raise ResolutionError(f"cannot interrupt terminal install state {self.state.value}")
        return self.rollback(f"interrupted:{phase}")
