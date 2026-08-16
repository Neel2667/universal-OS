"""Bootstrap Capsule contracts and fail-closed preliminary selection.

This module plans a capsule selection only. It has no downloader, USB transport,
flasher, partition writer, or reboot command.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from .contracts import ARCHITECTURES, _mapping, _require_keys, _string
from .discovery import DiscoveryRecord, PARTITION_MODELS, TRANSPORTS
from .errors import ContractError, ResolutionError, TrustError
from .trust import TrustVerifier
from .versioning import parse_version


def _string_set(value: Any, name: str) -> frozenset[str]:
    if not isinstance(value, list) or not value:
        raise ContractError(f"{name} must be a non-empty array")
    items = frozenset(_string(item, f"{name} item") for item in value)
    if len(items) != len(value):
        raise ContractError(f"{name} must contain unique values")
    return items


@dataclass(frozen=True)
class BootstrapCapsule:
    """A minimal board-compatible discovery/recovery adapter manifest."""

    capsule_id: str
    version: str
    architectures: frozenset[str]
    board_families: frozenset[str]
    soc_families: frozenset[str]
    partition_models: frozenset[str]
    transports: frozenset[str]
    sha256: str
    bytes: int
    offline_recovery: bool
    log_export: bool
    signer: str
    signature: str
    expires: datetime

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "BootstrapCapsule":
        _require_keys(
            raw,
            "bootstrap capsule",
            frozenset({"schema_version", "capsule_id", "version", "compatibility", "payload", "recovery", "security"}),
            frozenset({"schema_version", "capsule_id", "version", "compatibility", "payload", "recovery", "security"}),
        )
        if raw["schema_version"] != 1:
            raise ContractError("bootstrap capsule schema_version must be 1")
        version = _string(raw["version"], "bootstrap capsule.version")
        parse_version(version)

        compatibility = _mapping(raw["compatibility"], "bootstrap capsule.compatibility")
        _require_keys(
            compatibility,
            "bootstrap capsule.compatibility",
            frozenset({"architectures", "board_families", "soc_families", "partition_models", "transports"}),
            frozenset({"architectures", "board_families", "soc_families", "partition_models", "transports"}),
        )
        architectures = _string_set(compatibility["architectures"], "bootstrap capsule.compatibility.architectures")
        if not architectures <= ARCHITECTURES:
            raise ContractError("bootstrap capsule contains unsupported architecture")
        board_families = _string_set(compatibility["board_families"], "bootstrap capsule.compatibility.board_families")
        soc_families = _string_set(compatibility["soc_families"], "bootstrap capsule.compatibility.soc_families")
        if "*" in board_families or "*" in soc_families:
            raise ContractError("bootstrap capsule must not use wildcard board or SoC matching")
        partition_models = _string_set(compatibility["partition_models"], "bootstrap capsule.compatibility.partition_models")
        if not partition_models <= PARTITION_MODELS:
            raise ContractError("bootstrap capsule contains unsupported partition model")
        transports = _string_set(compatibility["transports"], "bootstrap capsule.compatibility.transports")
        if not transports <= TRANSPORTS:
            raise ContractError("bootstrap capsule contains unsupported transport")

        payload = _mapping(raw["payload"], "bootstrap capsule.payload")
        _require_keys(payload, "bootstrap capsule.payload", frozenset({"sha256", "bytes", "install_mode"}), frozenset({"sha256", "bytes", "install_mode"}))
        digest = _string(payload["sha256"], "bootstrap capsule.payload.sha256")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ContractError("bootstrap capsule payload must declare a lowercase SHA-256 digest")
        bytes_value = payload["bytes"]
        if not isinstance(bytes_value, int) or bytes_value <= 0:
            raise ContractError("bootstrap capsule payload bytes must be a positive integer")
        if payload["install_mode"] != "bootstrap-capsule":
            raise ContractError("bootstrap capsule install_mode must be 'bootstrap-capsule'")

        recovery = _mapping(raw["recovery"], "bootstrap capsule.recovery")
        _require_keys(recovery, "bootstrap capsule.recovery", frozenset({"offline_recovery", "log_export"}), frozenset({"offline_recovery", "log_export"}))
        if recovery["offline_recovery"] is not True:
            raise ContractError("bootstrap capsule must support offline recovery")
        if not isinstance(recovery["log_export"], bool):
            raise ContractError("bootstrap capsule recovery.log_export must be boolean")

        security = _mapping(raw["security"], "bootstrap capsule.security")
        _require_keys(security, "bootstrap capsule.security", frozenset({"signer", "signature", "expires"}), frozenset({"signer", "signature", "expires"}))
        try:
            expires = datetime.fromisoformat(_string(security["expires"], "bootstrap capsule.security.expires").replace("Z", "+00:00"))
        except ValueError as exc:
            raise ContractError("bootstrap capsule expiry must be an ISO-8601 timestamp") from exc
        if expires.tzinfo is None:
            raise ContractError("bootstrap capsule expiry must include a timezone")

        return cls(
            capsule_id=_string(raw["capsule_id"], "bootstrap capsule.capsule_id"),
            version=version,
            architectures=architectures,
            board_families=board_families,
            soc_families=soc_families,
            partition_models=partition_models,
            transports=transports,
            sha256=digest,
            bytes=bytes_value,
            offline_recovery=True,
            log_export=recovery["log_export"],
            signer=_string(security["signer"], "bootstrap capsule.security.signer"),
            signature=_string(security["signature"], "bootstrap capsule.security.signature"),
            expires=expires,
        )


@dataclass(frozen=True)
class BootstrapRejection:
    capsule_id: str
    reason: str


@dataclass(frozen=True)
class BootstrapPlan:
    """Selection result for an installer; contains no executable installation action."""

    discovery_record_id: str
    capsule: BootstrapCapsule
    rejections: tuple[BootstrapRejection, ...]


def _matches(record: DiscoveryRecord, capsule: BootstrapCapsule) -> str | None:
    if record.architecture not in capsule.architectures:
        return "architecture mismatch"
    if record.board_family not in capsule.board_families:
        return "board family mismatch"
    if record.soc_family not in capsule.soc_families:
        return "SoC family mismatch"
    if record.partition_model not in capsule.partition_models:
        return "partition model mismatch"
    if record.transport not in capsule.transports:
        return "transport mismatch"
    return None


def select_bootstrap(
    record: DiscoveryRecord,
    capsules: Iterable[BootstrapCapsule],
    verifier: TrustVerifier,
    *,
    now: datetime | None = None,
) -> BootstrapPlan:
    """Fail closed unless one unambiguous trusted capsule matches preliminary facts."""
    if record.bootloader_state != "unlocked":
        raise ResolutionError("Discovery Base cannot be installed: bootloader is not confirmed unlocked")
    timestamp = now or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise ResolutionError("selection time must include a timezone")

    candidates: list[BootstrapCapsule] = []
    rejections: list[BootstrapRejection] = []
    for capsule in capsules:
        try:
            verifier.verify(capsule, timestamp)
        except TrustError as exc:
            rejections.append(BootstrapRejection(capsule.capsule_id, f"trust rejected: {exc}"))
            continue
        mismatch = _matches(record, capsule)
        if mismatch:
            rejections.append(BootstrapRejection(capsule.capsule_id, mismatch))
            continue
        candidates.append(capsule)

    if not candidates:
        raise ResolutionError(f"no trusted Bootstrap Capsule matches discovery record {record.record_id}")
    newest_version = max(parse_version(item.version) for item in candidates)
    newest = [item for item in candidates if parse_version(item.version) == newest_version]
    if len(newest) != 1:
        ids = ", ".join(sorted(item.capsule_id for item in newest))
        raise ResolutionError(f"ambiguous newest Bootstrap Capsule selection: {ids}")
    return BootstrapPlan(record.record_id, newest[0], tuple(rejections))
