"""Parsing and structural validation for v1 portable-core contracts.

The JSON Schemas in specs/ are the normative interchange description. These
functions mirror the security-critical subset without third-party dependencies
so the first resolver can be exercised in a clean Python environment.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, FrozenSet, Mapping, Tuple

from .errors import ContractError
from .versioning import parse_version

ARCHITECTURES = frozenset({"arm64", "armv7", "x86_64", "riscv64"})
SUPPORT_TIERS = frozenset({"profiled", "lab", "verified", "maintained", "retired"})
CAPABILITY_STATES = frozenset({"working", "partial", "unavailable", "untested", "blocked", "unsafe"})
INSTALL_MODES = frozenset({"inactive-slot", "transactional", "user-space"})


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{name} must be an object")
    return value


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{name} must be a non-empty string")
    return value


def _require_keys(value: Mapping[str, Any], name: str, required: FrozenSet[str], allowed: FrozenSet[str]) -> None:
    missing = required - value.keys()
    unknown = value.keys() - allowed
    if missing:
        raise ContractError(f"{name} missing required fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ContractError(f"{name} has unknown fields: {', '.join(sorted(unknown))}")


@dataclass(frozen=True)
class HardwareProfile:
    profile_id: str
    display_name: str
    support_tier: str
    architecture: str
    board_family: str
    soc_family: str
    bootstrap_version: str
    kernel_abi: str
    partition_model: str
    verified_boot: str
    rollback_protection: str
    capabilities: Mapping[str, str]
    required_components: Tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "HardwareProfile":
        _require_keys(
            raw,
            "profile",
            frozenset({"schema_version", "profile_id", "display_name", "support_tier", "architecture", "hardware", "boot", "capabilities", "device_support"}),
            frozenset({"schema_version", "profile_id", "display_name", "support_tier", "architecture", "hardware", "boot", "capabilities", "device_support"}),
        )
        if raw["schema_version"] != 1:
            raise ContractError("profile schema_version must be 1")
        architecture = _string(raw["architecture"], "profile.architecture")
        if architecture not in ARCHITECTURES:
            raise ContractError(f"unsupported architecture: {architecture}")
        tier = _string(raw["support_tier"], "profile.support_tier")
        if tier not in SUPPORT_TIERS:
            raise ContractError(f"invalid support tier: {tier}")

        hardware = _mapping(raw["hardware"], "profile.hardware")
        _require_keys(hardware, "profile.hardware", frozenset({"board_family", "soc_family"}), frozenset({"board_family", "soc_family", "revision_range"}))
        boot = _mapping(raw["boot"], "profile.boot")
        _require_keys(
            boot,
            "profile.boot",
            frozenset({"bootstrap_version", "kernel_abi", "partition_model", "verified_boot", "rollback_protection"}),
            frozenset({"bootstrap_version", "kernel_abi", "partition_model", "verified_boot", "rollback_protection"}),
        )
        version = _string(boot["bootstrap_version"], "profile.boot.bootstrap_version")
        parse_version(version)
        partition_model = _string(boot["partition_model"], "profile.boot.partition_model")
        if partition_model not in {"ab", "transactional", "single-slot"}:
            raise ContractError(f"invalid partition model: {partition_model}")

        capabilities = _mapping(raw["capabilities"], "profile.capabilities")
        if not capabilities:
            raise ContractError("profile.capabilities must not be empty")
        for name, state in capabilities.items():
            _string(name, "profile.capabilities key")
            if state not in CAPABILITY_STATES:
                raise ContractError(f"invalid capability state for {name}: {state!r}")

        device_support = _mapping(raw["device_support"], "profile.device_support")
        _require_keys(device_support, "profile.device_support", frozenset({"required_components"}), frozenset({"required_components", "provenance_state"}))
        components = device_support["required_components"]
        if not isinstance(components, list) or any(not isinstance(item, str) or not item for item in components):
            raise ContractError("profile.device_support.required_components must be a string array")
        if len(set(components)) != len(components):
            raise ContractError("profile.device_support.required_components must be unique")

        return cls(
            profile_id=_string(raw["profile_id"], "profile.profile_id"),
            display_name=_string(raw["display_name"], "profile.display_name"),
            support_tier=tier,
            architecture=architecture,
            board_family=_string(hardware["board_family"], "profile.hardware.board_family"),
            soc_family=_string(hardware["soc_family"], "profile.hardware.soc_family"),
            bootstrap_version=version,
            kernel_abi=_string(boot["kernel_abi"], "profile.boot.kernel_abi"),
            partition_model=partition_model,
            verified_boot=_string(boot["verified_boot"], "profile.boot.verified_boot"),
            rollback_protection=_string(boot["rollback_protection"], "profile.boot.rollback_protection"),
            capabilities=dict(capabilities),
            required_components=tuple(components),
        )


@dataclass(frozen=True)
class PackageManifest:
    package_id: str
    version: str
    kind: str
    component: str
    architectures: FrozenSet[str]
    profile_ids: FrozenSet[str]
    kernel_abi: str | None
    bootstrap_version_range: str
    required_capabilities: Mapping[str, str]
    sha256: str
    bytes: int
    install_mode: str
    signer: str
    signature: str
    expires: datetime

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "PackageManifest":
        _require_keys(
            raw,
            "package",
            frozenset({"schema_version", "package_id", "version", "kind", "provides", "compatibility", "payload", "security"}),
            frozenset({"schema_version", "package_id", "version", "kind", "provides", "compatibility", "payload", "security"}),
        )
        if raw["schema_version"] != 1:
            raise ContractError("package schema_version must be 1")
        version = _string(raw["version"], "package.version")
        parse_version(version)
        kind = _string(raw["kind"], "package.kind")
        if kind not in {"core", "device-support"}:
            raise ContractError(f"invalid package kind: {kind}")

        provides = _mapping(raw["provides"], "package.provides")
        _require_keys(provides, "package.provides", frozenset({"component"}), frozenset({"component"}))
        compatibility = _mapping(raw["compatibility"], "package.compatibility")
        _require_keys(
            compatibility,
            "package.compatibility",
            frozenset({"architectures", "profile_ids", "bootstrap_version_range"}),
            frozenset({"architectures", "profile_ids", "kernel_abi", "bootstrap_version_range", "required_capabilities"}),
        )
        architectures_value = compatibility["architectures"]
        if not isinstance(architectures_value, list) or not architectures_value:
            raise ContractError("package.compatibility.architectures must be a non-empty array")
        architectures = frozenset(_string(item, "package.compatibility.architectures item") for item in architectures_value)
        if not architectures <= ARCHITECTURES:
            raise ContractError("package.compatibility.architectures contains an unsupported architecture")
        profile_ids_value = compatibility["profile_ids"]
        if not isinstance(profile_ids_value, list) or not profile_ids_value:
            raise ContractError("package.compatibility.profile_ids must be a non-empty array")
        profile_ids = frozenset(_string(item, "package.compatibility.profile_ids item") for item in profile_ids_value)

        required_capabilities: Mapping[str, str] = {}
        if "required_capabilities" in compatibility:
            required_capabilities = _mapping(compatibility["required_capabilities"], "package.compatibility.required_capabilities")
            for capability, required_state in required_capabilities.items():
                _string(capability, "package.compatibility.required_capabilities key")
                if required_state != "working":
                    raise ContractError("v1 only permits 'working' required capability state")

        payload = _mapping(raw["payload"], "package.payload")
        _require_keys(payload, "package.payload", frozenset({"sha256", "bytes", "install_mode"}), frozenset({"sha256", "bytes", "install_mode"}))
        digest = _string(payload["sha256"], "package.payload.sha256")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ContractError("package.payload.sha256 must be a lowercase SHA-256 digest")
        byte_count = payload["bytes"]
        if not isinstance(byte_count, int) or byte_count < 0:
            raise ContractError("package.payload.bytes must be a non-negative integer")
        install_mode = _string(payload["install_mode"], "package.payload.install_mode")
        if install_mode not in INSTALL_MODES:
            raise ContractError(f"invalid install mode: {install_mode}")

        security = _mapping(raw["security"], "package.security")
        _require_keys(security, "package.security", frozenset({"signer", "signature", "expires"}), frozenset({"signer", "signature", "expires"}))
        try:
            expires = datetime.fromisoformat(_string(security["expires"], "package.security.expires").replace("Z", "+00:00"))
        except ValueError as exc:
            raise ContractError("package.security.expires must be an ISO-8601 timestamp") from exc
        if expires.tzinfo is None:
            raise ContractError("package.security.expires must include a timezone")

        return cls(
            package_id=_string(raw["package_id"], "package.package_id"),
            version=version,
            kind=kind,
            component=_string(provides["component"], "package.provides.component"),
            architectures=architectures,
            profile_ids=profile_ids,
            kernel_abi=compatibility.get("kernel_abi"),
            bootstrap_version_range=_string(compatibility["bootstrap_version_range"], "package.compatibility.bootstrap_version_range"),
            required_capabilities=dict(required_capabilities),
            sha256=digest,
            bytes=byte_count,
            install_mode=install_mode,
            signer=_string(security["signer"], "package.security.signer"),
            signature=_string(security["signature"], "package.security.signature"),
            expires=expires,
        )
