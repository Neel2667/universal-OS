"""Architecture-independent UniversalOS service boundary.

This is the host-side reference API between the shared UniversalOS core/UI and
future device-enablement packages. It coordinates only already verified inputs
and local model stores. It never opens a network connection, executes a driver,
invokes a bootloader, or writes a phone partition.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

from .artifacts import VerifiedTargetArtifact
from .contracts import HardwareProfile
from .errors import ResolutionError
from .health import HealthPolicy, HealthReport, health_is_confirmed
from .install import InstallJournal, InstallState
from .persistence import JournalStore, StagedArtifact, StagingStore
from .preflight import DeviceConditions, PreflightPolicy, PreflightResult, evaluate_preflight
from .resolver import ResolutionPlan, resolve_verified_manifests


class UpdateBlockedError(ResolutionError):
    """An update could not start because a safe precondition was not met."""


@dataclass(frozen=True)
class DeviceStatus:
    """Non-personal status exposed to a future settings/UI surface."""

    profile_id: str
    support_tier: str
    architecture: str
    partition_model: str
    capabilities: Mapping[str, str]
    active_target: str
    update_state: str


@dataclass(frozen=True)
class StagedUpdate:
    """A fully verified but not yet booted host-side installation transaction."""

    resolution: ResolutionPlan
    journal: InstallJournal
    staged_artifacts: tuple[StagedArtifact, ...]
    preflight: PreflightResult


@dataclass(frozen=True)
class RecoveryReport:
    """Redacted, local recovery information with no paths, payloads, or identifiers."""

    profile_id: str
    state: str
    active_target: str
    staged_target: str | None
    package_count: int
    events: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(
            {
                "profile_id": self.profile_id,
                "state": self.state,
                "active_target": self.active_target,
                "staged_target": self.staged_target,
                "package_count": self.package_count,
                "events": list(self.events),
            },
            sort_keys=True,
            separators=(",", ":"),
        )


class UniversalSystemServices:
    """Coordinates generic profile/update/preflight/staging/health/recovery contracts.

    A real device adapter would provide measured conditions, verified artifacts,
    persistent-device paths, and authenticated health reports. This class is
    deliberately unaware of device model names and contains no hardware driver
    or transport code.
    """

    def __init__(
        self,
        profile: HardwareProfile,
        *,
        active_target: str,
        journal_directory: Path,
        staging_directory: Path,
        health_policy: HealthPolicy,
        preflight_policy: PreflightPolicy = PreflightPolicy(),
    ) -> None:
        self.profile = profile
        self.active_target = active_target
        self.journal_store = JournalStore(journal_directory)
        self.staging_store = StagingStore(staging_directory)
        self.health_policy = health_policy
        self.preflight_policy = preflight_policy

    def status(self) -> DeviceStatus:
        try:
            journal = self.journal_store.load().journal
            active_target = journal.active_target
            update_state = journal.state.value
        except Exception:
            active_target = self.active_target
            update_state = InstallState.IDLE.value
        return DeviceStatus(
            self.profile.profile_id,
            self.profile.support_tier,
            self.profile.architecture,
            self.profile.partition_model,
            dict(self.profile.capabilities),
            active_target,
            update_state,
        )

    def stage_verified_update(
        self,
        artifacts: Iterable[VerifiedTargetArtifact],
        conditions: DeviceConditions,
    ) -> StagedUpdate:
        """Resolve, preflight, stage, and persist a transaction without booting it."""
        artifacts = tuple(artifacts)
        if not artifacts:
            raise UpdateBlockedError("no verified target artifacts were supplied")
        resolution = resolve_verified_manifests(self.profile, [artifact.manifest for artifact in artifacts])
        selected_ids = {resolution.core.package_id, *(item.package_id for item in resolution.device_support)}
        selected = tuple(artifact for artifact in artifacts if artifact.manifest.package_id in selected_ids)
        if {artifact.manifest.package_id for artifact in selected} != selected_ids:
            raise UpdateBlockedError("resolved package set is not fully backed by verified target artifacts")
        preflight = evaluate_preflight(self.profile, [artifact.target.payload_bytes for artifact in selected], conditions, self.preflight_policy)
        if not preflight.allowed:
            raise UpdateBlockedError("preflight blocked update: " + ",".join(preflight.reasons))

        journal = InstallJournal.begin(self.profile, self.active_target).metadata_verified()
        self.journal_store.save(journal)
        staged = tuple(
            self.staging_store.stage(
                artifact.target.target_id,
                artifact.target.package_id,
                artifact.target.payload_sha256,
                artifact.payload,
            )
            for artifact in selected
        )
        journal = journal.artifacts_verified(artifact.target.package_id for artifact in selected).stage()
        self.journal_store.save(journal)
        return StagedUpdate(resolution, journal, staged, preflight)

    def request_first_boot(self) -> InstallJournal:
        journal = self.journal_store.load().journal.request_first_boot()
        self.journal_store.save(journal)
        return journal

    def confirm_first_boot(self, report: HealthReport, *, now: datetime | None = None) -> InstallJournal:
        journal = self.journal_store.load().journal
        if journal.state != InstallState.PENDING_FIRST_BOOT or journal.staged_target is None:
            raise ResolutionError("no staged first boot is awaiting health confirmation")
        timestamp = now or datetime.now(timezone.utc)
        healthy = health_is_confirmed(
            report,
            self.health_policy,
            expected_profile_id=self.profile.profile_id,
            expected_boot_target=journal.staged_target,
            now=timestamp,
        )
        journal = journal.confirm_health(healthy)
        self.journal_store.save(journal)
        return journal

    def recover(self, reason: str) -> InstallJournal:
        """Return to known-good modeled state when a transaction has altered nothing final."""
        journal = self.journal_store.load().journal
        if journal.state in {InstallState.ARTIFACTS_VERIFIED, InstallState.STAGED, InstallState.PENDING_FIRST_BOOT}:
            journal = journal.rollback(reason)
            self.journal_store.save(journal)
            return journal
        if journal.state == InstallState.ROLLED_BACK:
            return journal
        raise ResolutionError(f"recovery cannot roll back state {journal.state.value}")

    def recovery_report(self) -> RecoveryReport:
        journal = self.journal_store.load().journal
        return RecoveryReport(
            journal.profile_id,
            journal.state.value,
            journal.active_target,
            journal.staged_target,
            len(journal.package_ids),
            journal.events,
        )
