"""Signed hardware-profile catalog and fail-closed local profile selection.

The discovery-base facts are local and non-personal. A profiles metadata server
may supply candidates, but it cannot select a profile unless exact local match
rules and signature verification both pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from .contracts import ARCHITECTURES, HardwareProfile, _mapping, _require_keys, _string
from .errors import ContractError, ResolutionError
from .registry import MetadataState, SignedMetadata, TrustRoot, verify_and_accept

PARTITION_MODELS = frozenset({"ab", "transactional", "single-slot"})


@dataclass(frozen=True)
class MeasuredHardwareFacts:
    """Facts measured only after the local Discovery Base has booted."""

    architecture: str
    board_family: str
    soc_family: str
    revision_class: str
    partition_model: str
    kernel_abi: str

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "MeasuredHardwareFacts":
        _require_keys(
            raw,
            "measured hardware facts",
            frozenset({"schema_version", "architecture", "board_family", "soc_family", "revision_class", "partition_model", "kernel_abi"}),
            frozenset({"schema_version", "architecture", "board_family", "soc_family", "revision_class", "partition_model", "kernel_abi"}),
        )
        if raw["schema_version"] != 1:
            raise ContractError("measured hardware facts schema_version must be 1")
        architecture = _string(raw["architecture"], "measured hardware facts.architecture")
        if architecture not in ARCHITECTURES:
            raise ContractError("measured hardware facts has unsupported architecture")
        partition_model = _string(raw["partition_model"], "measured hardware facts.partition_model")
        if partition_model not in PARTITION_MODELS:
            raise ContractError("measured hardware facts has unsupported partition model")
        return cls(
            architecture,
            _string(raw["board_family"], "measured hardware facts.board_family"),
            _string(raw["soc_family"], "measured hardware facts.soc_family"),
            _string(raw["revision_class"], "measured hardware facts.revision_class"),
            partition_model,
            _string(raw["kernel_abi"], "measured hardware facts.kernel_abi"),
        )


def _string_set(value: Any, name: str, *, permit_revision_wildcard: bool = False) -> frozenset[str]:
    if not isinstance(value, list) or not value:
        raise ContractError(f"{name} must be a non-empty array")
    items = frozenset(_string(item, f"{name} item") for item in value)
    if len(items) != len(value):
        raise ContractError(f"{name} must contain unique entries")
    if "*" in items and not permit_revision_wildcard:
        raise ContractError(f"{name} must not contain wildcard entries")
    return items


@dataclass(frozen=True)
class ProfileCatalogEntry:
    profile: HardwareProfile
    board_families: frozenset[str]
    soc_families: frozenset[str]
    revision_classes: frozenset[str]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ProfileCatalogEntry":
        _require_keys(raw, "profile catalog entry", frozenset({"profile", "match"}), frozenset({"profile", "match"}))
        profile = HardwareProfile.from_dict(_mapping(raw["profile"], "profile catalog entry.profile"))
        match = _mapping(raw["match"], "profile catalog entry.match")
        _require_keys(match, "profile catalog entry.match", frozenset({"board_families", "soc_families", "revision_classes"}), frozenset({"board_families", "soc_families", "revision_classes"}))
        boards = _string_set(match["board_families"], "profile catalog match.board_families")
        socs = _string_set(match["soc_families"], "profile catalog match.soc_families")
        revisions = _string_set(match["revision_classes"], "profile catalog match.revision_classes", permit_revision_wildcard=True)
        return cls(profile, boards, socs, revisions)

    def matches(self, facts: MeasuredHardwareFacts) -> bool:
        return (
            facts.architecture == self.profile.architecture
            and facts.board_family in self.board_families
            and facts.soc_family in self.soc_families
            and ("*" in self.revision_classes or facts.revision_class in self.revision_classes)
            and facts.partition_model == self.profile.partition_model
            and facts.kernel_abi == self.profile.kernel_abi
        )


@dataclass(frozen=True)
class ProfileCatalog:
    entries: tuple[ProfileCatalogEntry, ...]

    @classmethod
    def from_metadata(cls, metadata: SignedMetadata) -> "ProfileCatalog":
        if metadata.role != "profiles":
            raise ContractError("ProfileCatalog requires verified role=profiles metadata")
        _require_keys(metadata.signed, "profiles signed body", frozenset({"profiles"}), frozenset({"profiles"}))
        profiles = metadata.signed["profiles"]
        if not isinstance(profiles, list) or not profiles:
            raise ContractError("profiles signed body.profiles must be a non-empty array")
        entries = tuple(ProfileCatalogEntry.from_dict(_mapping(raw, "profiles catalog entry")) for raw in profiles)
        ids = {entry.profile.profile_id for entry in entries}
        if len(ids) != len(entries):
            raise ContractError("profiles catalog contains duplicate profile ids")
        return cls(entries)

    def select(self, facts: MeasuredHardwareFacts) -> HardwareProfile:
        matches = [entry.profile for entry in self.entries if entry.matches(facts)]
        if not matches:
            raise ResolutionError("no signed hardware profile matches locally measured facts")
        if len(matches) > 1:
            raise ResolutionError("ambiguous signed hardware profile match")
        return matches[0]


def verify_and_load_profiles(
    root: TrustRoot,
    metadata: SignedMetadata,
    state: MetadataState,
    *,
    now: datetime,
) -> tuple[ProfileCatalog, MetadataState]:
    """Verify signed profiles metadata before the catalog becomes usable."""
    next_state = verify_and_accept(root, metadata, "profiles", state, now)
    return ProfileCatalog.from_metadata(metadata), next_state
