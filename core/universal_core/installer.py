"""End-to-end host-side UniversalOS USB/offline installer rehearsal.

This coordinator intentionally has no bootloader, USB, network, or partition
implementation. It chains the same signed-catalog and transfer contracts that a
future native Universal Installer/Discovery Base must use, making skipped trust
or profile stages visible in one deterministic integration path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping

from .artifacts import TargetDescriptor, TargetsCatalog, VerifiedTargetArtifact, verify_target_artifact
from .bootstrap import BootstrapPlan, select_catalog_bootstrap, verify_and_load_bootstrap_catalog
from .discovery import DiscoveryRecord
from .errors import ResolutionError
from .profiles import MeasuredHardwareFacts, ProfileCatalog, verify_and_load_profiles
from .registry import MetadataState, SignedMetadata, TrustRoot, verify_and_accept
from .transfer import CompletedTransfer, ResumableTransferStore, TransferManifest


class InstallerPhase(str, Enum):
    NEW = "new"
    BOOTSTRAP_SELECTED = "bootstrap-selected"
    PROFILE_SELECTED = "profile-selected"
    TARGETS_VERIFIED = "targets-verified"
    ARTIFACTS_READY = "artifacts-ready"


@dataclass(frozen=True)
class InstallerStatus:
    phase: InstallerPhase
    bootstrap_id: str | None
    profile_id: str | None
    ready_artifact_ids: tuple[str, ...]


class UniversalInstallerRehearsal:
    """Fails closed through bootstrap, profile, targets, and transfer stages."""

    def __init__(
        self,
        root: TrustRoot,
        discovery: DiscoveryRecord,
        measured_facts: MeasuredHardwareFacts,
        transfer_directory: Path,
        *,
        now: datetime,
    ) -> None:
        self.root = root
        self.discovery = discovery
        self.measured_facts = measured_facts
        self.transfer_directory = transfer_directory.resolve()
        self.now = now
        self.metadata_state = MetadataState.empty()
        self.phase = InstallerPhase.NEW
        self.bootstrap_plan: BootstrapPlan | None = None
        self.profile_catalog: ProfileCatalog | None = None
        self.profile_id: str | None = None
        self.targets_catalog: TargetsCatalog | None = None
        self._transfer_data: dict[tuple[str, str], bytes] = {}
        self._artifacts: dict[str, VerifiedTargetArtifact] = {}

    def status(self) -> InstallerStatus:
        return InstallerStatus(
            self.phase,
            self.bootstrap_plan.capsule.capsule_id if self.bootstrap_plan else None,
            self.profile_id,
            tuple(sorted(self._artifacts)),
        )

    def select_bootstrap(self, metadata: SignedMetadata) -> BootstrapPlan:
        self._require(InstallerPhase.NEW)
        catalog, self.metadata_state = verify_and_load_bootstrap_catalog(self.root, metadata, self.metadata_state, now=self.now)
        self.bootstrap_plan = select_catalog_bootstrap(self.discovery, catalog)
        self.phase = InstallerPhase.BOOTSTRAP_SELECTED
        return self.bootstrap_plan

    def select_profile(self, metadata: SignedMetadata) -> str:
        self._require(InstallerPhase.BOOTSTRAP_SELECTED)
        self.profile_catalog, self.metadata_state = verify_and_load_profiles(self.root, metadata, self.metadata_state, now=self.now)
        profile = self.profile_catalog.select(self.measured_facts)
        self.profile_id = profile.profile_id
        self.phase = InstallerPhase.PROFILE_SELECTED
        return profile.profile_id

    def verify_targets(self, metadata: SignedMetadata) -> TargetsCatalog:
        self._require(InstallerPhase.PROFILE_SELECTED)
        self.metadata_state = verify_and_accept(self.root, metadata, "targets", self.metadata_state, self.now)
        self.targets_catalog = TargetsCatalog.from_metadata(metadata)
        self.phase = InstallerPhase.TARGETS_VERIFIED
        return self.targets_catalog

    def receive(self, manifest: TransferManifest, chunks: Mapping[int, bytes]) -> CompletedTransfer | None:
        """Accept verified chunks; return completion only after full artifact validation."""
        self._require_at_least(InstallerPhase.TARGETS_VERIFIED)
        assert self.targets_catalog is not None
        descriptor = self.targets_catalog.descriptors.get(manifest.target_id)
        if descriptor is None:
            raise ResolutionError("transfer target is not in verified targets catalog")
        store = ResumableTransferStore(self.transfer_directory, manifest, descriptor)
        for index, data in chunks.items():
            store.receive_chunk(index, data)
        if store.missing_chunks:
            return None
        completed = store.finalize()
        self._transfer_data[(manifest.target_id, manifest.artifact_kind)] = completed.path.read_bytes()
        self._try_bind_artifact(descriptor)
        return completed

    def artifact(self, target_id: str) -> VerifiedTargetArtifact:
        try:
            return self._artifacts[target_id]
        except KeyError as exc:
            raise ResolutionError("target has not completed both verified manifest and payload transfer") from exc

    def artifacts(self) -> tuple[VerifiedTargetArtifact, ...]:
        if self._artifacts:
            self.phase = InstallerPhase.ARTIFACTS_READY
        return tuple(self._artifacts[target_id] for target_id in sorted(self._artifacts))

    def _try_bind_artifact(self, descriptor: TargetDescriptor) -> None:
        manifest = self._transfer_data.get((descriptor.target_id, "manifest"))
        payload = self._transfer_data.get((descriptor.target_id, "payload"))
        if manifest is not None and payload is not None:
            self._artifacts[descriptor.target_id] = verify_target_artifact(self.targets_catalog, descriptor.target_id, manifest, payload)  # type: ignore[arg-type]

    def _require(self, phase: InstallerPhase) -> None:
        if self.phase != phase:
            raise ResolutionError(f"installer phase must be {phase.value}, is {self.phase.value}")

    def _require_at_least(self, phase: InstallerPhase) -> None:
        order = list(InstallerPhase)
        if order.index(self.phase) < order.index(phase):
            raise ResolutionError(f"installer phase must reach {phase.value}, is {self.phase.value}")
