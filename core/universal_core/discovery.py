"""Preliminary, non-personal discovery contract for Universal Installer inputs.

A DiscoveryRecord is deliberately not final device trust. It is a bounded set of
facts from an allowed local transport used to select a minimal Bootstrap Capsule.
Discovery Base must re-measure relevant facts locally before full-system install.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .contracts import ARCHITECTURES, _mapping, _require_keys, _string
from .errors import ContractError

TRANSPORTS = frozenset({"fastboot", "recovery", "adb"})
PARTITION_MODELS = frozenset({"ab", "transactional", "single-slot"})
BOOTLOADER_STATES = frozenset({"unlocked", "locked", "unknown"})


@dataclass(frozen=True)
class DiscoveryRecord:
    """Sanitized preliminary facts used only for bootstrap compatibility."""

    record_id: str
    architecture: str
    board_family: str
    soc_family: str
    revision_class: str | None
    bootloader_state: str
    partition_model: str
    transport: str

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "DiscoveryRecord":
        _require_keys(
            raw,
            "discovery record",
            frozenset({"schema_version", "record_id", "architecture", "hardware", "boot", "transport"}),
            frozenset({"schema_version", "record_id", "architecture", "hardware", "boot", "transport"}),
        )
        if raw["schema_version"] != 1:
            raise ContractError("discovery record schema_version must be 1")
        architecture = _string(raw["architecture"], "discovery record.architecture")
        if architecture not in ARCHITECTURES:
            raise ContractError(f"unsupported discovery architecture: {architecture}")

        hardware = _mapping(raw["hardware"], "discovery record.hardware")
        _require_keys(
            hardware,
            "discovery record.hardware",
            frozenset({"board_family", "soc_family"}),
            frozenset({"board_family", "soc_family", "revision_class"}),
        )
        boot = _mapping(raw["boot"], "discovery record.boot")
        _require_keys(
            boot,
            "discovery record.boot",
            frozenset({"bootloader_state", "partition_model"}),
            frozenset({"bootloader_state", "partition_model"}),
        )
        bootloader_state = _string(boot["bootloader_state"], "discovery record.boot.bootloader_state")
        if bootloader_state not in BOOTLOADER_STATES:
            raise ContractError(f"invalid bootloader state: {bootloader_state}")
        partition_model = _string(boot["partition_model"], "discovery record.boot.partition_model")
        if partition_model not in PARTITION_MODELS:
            raise ContractError(f"invalid discovery partition model: {partition_model}")

        transport = _mapping(raw["transport"], "discovery record.transport")
        _require_keys(transport, "discovery record.transport", frozenset({"protocol"}), frozenset({"protocol"}))
        protocol = _string(transport["protocol"], "discovery record.transport.protocol")
        if protocol not in TRANSPORTS:
            raise ContractError(f"unsupported discovery transport: {protocol}")

        revision = hardware.get("revision_class")
        if revision is not None:
            revision = _string(revision, "discovery record.hardware.revision_class")
        return cls(
            record_id=_string(raw["record_id"], "discovery record.record_id"),
            architecture=architecture,
            board_family=_string(hardware["board_family"], "discovery record.hardware.board_family"),
            soc_family=_string(hardware["soc_family"], "discovery record.hardware.soc_family"),
            revision_class=revision,
            bootloader_state=bootloader_state,
            partition_model=partition_model,
            transport=protocol,
        )
