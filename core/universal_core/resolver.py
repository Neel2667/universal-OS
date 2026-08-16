"""Profile-driven compatibility resolver for the UniversalOS core prototype."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping, Sequence

from .contracts import HardwareProfile, PackageManifest
from .errors import ResolutionError, TrustError
from .trust import TrustVerifier
from .versioning import is_in_range, parse_version


@dataclass(frozen=True)
class Rejection:
    package_id: str
    reason: str


@dataclass(frozen=True)
class ResolutionPlan:
    """The selected packages and auditable rejections for one hardware profile."""

    profile_id: str
    core: PackageManifest
    device_support: tuple[PackageManifest, ...]
    rejections: tuple[Rejection, ...]


def _matches(profile: HardwareProfile, package: PackageManifest) -> str | None:
    if profile.architecture not in package.architectures:
        return "architecture mismatch"
    if "*" not in package.profile_ids and profile.profile_id not in package.profile_ids:
        return "profile mismatch"
    if not is_in_range(profile.bootstrap_version, package.bootstrap_version_range):
        return "bootstrap version is outside package range"
    if package.kernel_abi is not None and package.kernel_abi != profile.kernel_abi:
        return "kernel ABI mismatch"
    for name, expected in package.required_capabilities.items():
        if profile.capabilities.get(name) != expected:
            return f"required capability {name!r} is not {expected!r}"
    if package.install_mode == "inactive-slot" and profile.partition_model != "ab":
        return "inactive-slot package requires A/B partition model"
    if package.install_mode == "transactional" and profile.partition_model not in {"ab", "transactional"}:
        return "transactional package requires a transactional-capable partition model"
    return None


def _newest(packages: Sequence[PackageManifest]) -> PackageManifest:
    return max(packages, key=lambda item: parse_version(item.version))


def resolve(
    profile: HardwareProfile,
    manifests: Iterable[PackageManifest],
    verifier: TrustVerifier,
    *,
    now: datetime | None = None,
) -> ResolutionPlan:
    """Build a safe profile-specific plan without using any device model logic.

    Every manifest is parsed before this function is called. It is trusted and
    compatibility-checked locally. Rejections are retained for audit/UI output;
    a lack of a trusted core or required device component is a hard failure.
    """
    timestamp = now or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise ResolutionError("resolution time must include a timezone")

    accepted: list[PackageManifest] = []
    rejections: list[Rejection] = []
    for manifest in manifests:
        try:
            verifier.verify(manifest, timestamp)
        except TrustError as exc:
            rejections.append(Rejection(manifest.package_id, f"trust rejected: {exc}"))
            continue
        mismatch = _matches(profile, manifest)
        if mismatch:
            rejections.append(Rejection(manifest.package_id, mismatch))
            continue
        accepted.append(manifest)

    cores = [item for item in accepted if item.kind == "core" and item.component == "core"]
    if not cores:
        raise ResolutionError(f"no trusted compatible core package for profile {profile.profile_id}")
    core = _newest(cores)

    support_by_component: dict[str, list[PackageManifest]] = {}
    for item in accepted:
        if item.kind == "device-support":
            support_by_component.setdefault(item.component, []).append(item)

    selected_support: list[PackageManifest] = []
    missing = []
    for component in profile.required_components:
        candidates = support_by_component.get(component, [])
        if not candidates:
            missing.append(component)
        else:
            selected_support.append(_newest(candidates))
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ResolutionError(f"missing trusted compatible device-support components: {missing_text}")

    return ResolutionPlan(
        profile_id=profile.profile_id,
        core=core,
        device_support=tuple(sorted(selected_support, key=lambda item: item.component)),
        rejections=tuple(rejections),
    )
