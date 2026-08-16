"""Bind verified targets metadata to exact manifest and payload bytes.

No downloader is implemented here. Callers supply already-obtained byte strings;
this module checks their hashes/lengths against previously verified role=targets
metadata before exposing a PackageManifest to the compatibility resolver.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from .contracts import PackageManifest, _mapping, _require_keys, _string
from .errors import ContractError, TrustError
from .registry import SignedMetadata


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digest_entry(raw: Mapping[str, Any], name: str) -> tuple[str, int]:
    _require_keys(raw, name, frozenset({"sha256", "bytes"}), frozenset({"sha256", "bytes"}))
    digest = _string(raw["sha256"], f"{name}.sha256")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ContractError(f"{name}.sha256 must be a lowercase SHA-256 digest")
    size = raw["bytes"]
    if not isinstance(size, int) or size < 0:
        raise ContractError(f"{name}.bytes must be a non-negative integer")
    return digest, size


@dataclass(frozen=True)
class TargetDescriptor:
    target_id: str
    package_id: str
    manifest_sha256: str
    manifest_bytes: int
    payload_sha256: str
    payload_bytes: int

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "TargetDescriptor":
        _require_keys(
            raw,
            "targets descriptor",
            frozenset({"target_id", "package_id", "manifest", "payload"}),
            frozenset({"target_id", "package_id", "manifest", "payload"}),
        )
        manifest_digest, manifest_size = _digest_entry(_mapping(raw["manifest"], "targets descriptor.manifest"), "targets descriptor.manifest")
        payload_digest, payload_size = _digest_entry(_mapping(raw["payload"], "targets descriptor.payload"), "targets descriptor.payload")
        if manifest_size < 1:
            raise ContractError("targets descriptor.manifest.bytes must be positive")
        return cls(
            target_id=_string(raw["target_id"], "targets descriptor.target_id"),
            package_id=_string(raw["package_id"], "targets descriptor.package_id"),
            manifest_sha256=manifest_digest,
            manifest_bytes=manifest_size,
            payload_sha256=payload_digest,
            payload_bytes=payload_size,
        )


@dataclass(frozen=True)
class TargetsCatalog:
    descriptors: Mapping[str, TargetDescriptor]

    @classmethod
    def from_metadata(cls, metadata: SignedMetadata) -> "TargetsCatalog":
        if metadata.role != "targets":
            raise ContractError("TargetsCatalog requires verified role=targets metadata")
        _require_keys(metadata.signed, "targets signed body", frozenset({"targets"}), frozenset({"targets"}))
        targets = metadata.signed["targets"]
        if not isinstance(targets, list) or not targets:
            raise ContractError("targets signed body.targets must be a non-empty array")
        descriptors = [TargetDescriptor.from_dict(_mapping(item, "targets signed body.targets item")) for item in targets]
        ids = {descriptor.target_id for descriptor in descriptors}
        if len(ids) != len(descriptors):
            raise ContractError("targets signed body has duplicate target ids")
        package_ids = {descriptor.package_id for descriptor in descriptors}
        if len(package_ids) != len(descriptors):
            raise ContractError("targets signed body has duplicate package ids")
        return cls({descriptor.target_id: descriptor for descriptor in descriptors})


@dataclass(frozen=True)
class VerifiedTargetArtifact:
    """A manifest/payload pair whose exact bytes match verified target metadata."""

    target: TargetDescriptor
    manifest: PackageManifest
    payload: bytes


def verify_target_artifact(catalog: TargetsCatalog, target_id: str, manifest_bytes: bytes, payload: bytes) -> VerifiedTargetArtifact:
    """Fail closed unless bytes match a descriptor and its parsed manifest agrees."""
    descriptor = catalog.descriptors.get(target_id)
    if descriptor is None:
        raise TrustError(f"target is absent from verified targets metadata: {target_id}")
    if len(manifest_bytes) != descriptor.manifest_bytes or _sha256(manifest_bytes) != descriptor.manifest_sha256:
        raise TrustError(f"manifest bytes do not match verified target descriptor: {target_id}")
    if len(payload) != descriptor.payload_bytes or _sha256(payload) != descriptor.payload_sha256:
        raise TrustError(f"payload bytes do not match verified target descriptor: {target_id}")
    try:
        raw_manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"target manifest is not valid UTF-8 JSON: {target_id}") from exc
    manifest = PackageManifest.from_dict(_mapping(raw_manifest, "target manifest"))
    if manifest.package_id != descriptor.package_id:
        raise TrustError(f"target descriptor package id mismatch: {target_id}")
    if manifest.sha256 != descriptor.payload_sha256 or manifest.bytes != descriptor.payload_bytes:
        raise TrustError(f"manifest payload digest/size is not bound to target descriptor: {target_id}")
    return VerifiedTargetArtifact(descriptor, manifest, payload)
