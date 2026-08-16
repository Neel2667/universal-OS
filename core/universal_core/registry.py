"""Canonical-JSON Ed25519 repository metadata reference implementation.

This module verifies signed *metadata envelopes*, not package payloads and not
boot images. It is intentionally host-side and does not download, write, flash,
or manage private production keys. Its narrow API lets the package/bootstrap
resolvers later receive a verified metadata set instead of test fixtures.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .contracts import _mapping, _require_keys, _string
from .errors import ContractError, TrustError

METADATA_ROLES = frozenset({"root", "targets", "bootstrap", "profiles"})


def _parse_timestamp(value: Any, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(_string(value, name).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ContractError(f"{name} must include a timezone")
    return parsed.astimezone(timezone.utc)


def canonical_json(value: Mapping[str, Any]) -> bytes:
    """Produce the exact canonical UTF-8 byte sequence used for Ed25519 signing."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def key_id_from_public_key(public_key: Ed25519PublicKey) -> str:
    """Return a stable non-secret key id from raw Ed25519 public bytes."""
    raw = public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return hashlib.sha256(raw).hexdigest()


def _base64_decode(value: str, name: str) -> bytes:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError, binascii.Error) as exc:
        raise ContractError(f"{name} must be valid base64") from exc


@dataclass(frozen=True)
class Signature:
    key_id: str
    value: bytes

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Signature":
        _require_keys(raw, "metadata signature", frozenset({"key_id", "signature"}), frozenset({"key_id", "signature"}))
        value = _base64_decode(_string(raw["signature"], "metadata signature.signature"), "metadata signature.signature")
        if len(value) != 64:
            raise ContractError("metadata signature must be an Ed25519 64-byte signature")
        return cls(_string(raw["key_id"], "metadata signature.key_id"), value)

    def to_dict(self) -> dict[str, str]:
        return {"key_id": self.key_id, "signature": base64.b64encode(self.value).decode("ascii")}


@dataclass(frozen=True)
class SignedMetadata:
    """A parsed envelope; canonical bytes exclude its signature list."""

    role: str
    version: int
    expires: datetime
    signed: Mapping[str, Any]
    signatures: tuple[Signature, ...]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "SignedMetadata":
        _require_keys(
            raw,
            "repository metadata",
            frozenset({"schema_version", "role", "version", "expires", "signed", "signatures"}),
            frozenset({"schema_version", "role", "version", "expires", "signed", "signatures"}),
        )
        if raw["schema_version"] != 1:
            raise ContractError("repository metadata schema_version must be 1")
        role = _string(raw["role"], "repository metadata.role")
        if role not in METADATA_ROLES:
            raise ContractError(f"unsupported repository metadata role: {role}")
        version = raw["version"]
        if not isinstance(version, int) or version < 1:
            raise ContractError("repository metadata.version must be a positive integer")
        signed = _mapping(raw["signed"], "repository metadata.signed")
        raw_signatures = raw["signatures"]
        if not isinstance(raw_signatures, list) or not raw_signatures:
            raise ContractError("repository metadata.signatures must be a non-empty array")
        signatures = tuple(Signature.from_dict(_mapping(item, "repository metadata.signatures item")) for item in raw_signatures)
        if len({signature.key_id for signature in signatures}) != len(signatures):
            raise ContractError("repository metadata must not contain duplicate signature key ids")
        return cls(role, version, _parse_timestamp(raw["expires"], "repository metadata.expires"), dict(signed), signatures)

    def signable_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "role": self.role,
            "version": self.version,
            "expires": self.expires.isoformat().replace("+00:00", "Z"),
            "signed": self.signed,
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json(self.signable_dict())

    def to_dict(self) -> dict[str, Any]:
        result = self.signable_dict()
        result["signatures"] = [signature.to_dict() for signature in self.signatures]
        return result

    def with_signature(self, key_id: str, private_key: Ed25519PrivateKey) -> "SignedMetadata":
        """Return a new envelope with an Ed25519 signature.

        This helper is for controlled test/release tooling only. It deliberately
        accepts an in-memory key object; production custody/threshold ceremony
        must live outside this repository and CI.
        """
        if key_id in {signature.key_id for signature in self.signatures}:
            raise ContractError(f"metadata already has a signature from key {key_id}")
        signature = Signature(key_id, private_key.sign(self.canonical_bytes()))
        return replace(self, signatures=(*self.signatures, signature))


@dataclass(frozen=True)
class TrustedKey:
    key_id: str
    public_key: Ed25519PublicKey

    @classmethod
    def from_dict(cls, key_id: str, raw: Mapping[str, Any]) -> "TrustedKey":
        _require_keys(raw, f"root key {key_id}", frozenset({"scheme", "public"}), frozenset({"scheme", "public"}))
        if raw["scheme"] != "ed25519":
            raise ContractError(f"root key {key_id} must use ed25519")
        public_bytes = _base64_decode(_string(raw["public"], f"root key {key_id}.public"), f"root key {key_id}.public")
        if len(public_bytes) != 32:
            raise ContractError(f"root key {key_id} must contain 32 raw Ed25519 public bytes")
        try:
            public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
        except ValueError as exc:
            raise ContractError(f"root key {key_id} is not a valid Ed25519 public key") from exc
        if key_id != key_id_from_public_key(public_key):
            raise ContractError(f"root key {key_id} does not match its public key material")
        return cls(key_id, public_key)

    def to_dict(self) -> dict[str, str]:
        raw = self.public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        return {"scheme": "ed25519", "public": base64.b64encode(raw).decode("ascii")}


@dataclass(frozen=True)
class RoleKeys:
    key_ids: frozenset[str]
    threshold: int


@dataclass(frozen=True)
class TrustRoot:
    """Trusted root configuration extracted from a verified root metadata envelope."""

    metadata: SignedMetadata
    keys: Mapping[str, TrustedKey]
    roles: Mapping[str, RoleKeys]

    @classmethod
    def from_metadata(cls, metadata: SignedMetadata) -> "TrustRoot":
        if metadata.role != "root":
            raise ContractError("TrustRoot must be built from role=root metadata")
        _require_keys(metadata.signed, "root signed body", frozenset({"keys", "roles"}), frozenset({"keys", "roles"}))
        raw_keys = _mapping(metadata.signed["keys"], "root signed body.keys")
        if not raw_keys:
            raise ContractError("root signed body.keys must not be empty")
        keys = {key_id: TrustedKey.from_dict(key_id, _mapping(value, f"root key {key_id}")) for key_id, value in raw_keys.items()}
        raw_roles = _mapping(metadata.signed["roles"], "root signed body.roles")
        if "root" not in raw_roles:
            raise ContractError("root signed body.roles must define the root role")
        roles: dict[str, RoleKeys] = {}
        for role, value in raw_roles.items():
            if role not in METADATA_ROLES:
                raise ContractError(f"root contains unsupported role {role}")
            role_value = _mapping(value, f"root role {role}")
            _require_keys(role_value, f"root role {role}", frozenset({"key_ids", "threshold"}), frozenset({"key_ids", "threshold"}))
            key_ids_value = role_value["key_ids"]
            if not isinstance(key_ids_value, list) or not key_ids_value:
                raise ContractError(f"root role {role}.key_ids must be non-empty")
            key_ids = frozenset(_string(item, f"root role {role}.key_ids item") for item in key_ids_value)
            if len(key_ids) != len(key_ids_value):
                raise ContractError(f"root role {role}.key_ids must be unique")
            if not key_ids <= keys.keys():
                raise ContractError(f"root role {role} names an unknown key")
            threshold = role_value["threshold"]
            if not isinstance(threshold, int) or threshold < 1 or threshold > len(key_ids):
                raise ContractError(f"root role {role} has an invalid threshold")
            roles[role] = RoleKeys(key_ids, threshold)
        return cls(metadata, keys, roles)

    @property
    def version(self) -> int:
        return self.metadata.version

    @property
    def expires(self) -> datetime:
        return self.metadata.expires


@dataclass(frozen=True)
class MetadataState:
    """Immutable accepted-version state used to reject metadata rollback attacks."""

    versions: Mapping[str, int]

    @classmethod
    def empty(cls) -> "MetadataState":
        return cls({})

    def accept(self, metadata: SignedMetadata) -> "MetadataState":
        current = self.versions.get(metadata.role, 0)
        if metadata.version <= current:
            raise TrustError(f"metadata rollback detected for role {metadata.role}: {metadata.version} <= {current}")
        updated = dict(self.versions)
        updated[metadata.role] = metadata.version
        return MetadataState(updated)


def verify_metadata(root: TrustRoot, metadata: SignedMetadata, expected_role: str, now: datetime) -> None:
    """Verify expiration, role, and threshold Ed25519 signatures against a root."""
    if now.tzinfo is None:
        raise TrustError("verification time must include a timezone")
    timestamp = now.astimezone(timezone.utc)
    if root.expires <= timestamp:
        raise TrustError("trusted root metadata is expired")
    if metadata.role != expected_role:
        raise TrustError(f"metadata role mismatch: expected {expected_role}, got {metadata.role}")
    if metadata.expires <= timestamp:
        raise TrustError(f"{expected_role} metadata is expired")
    role_keys = root.roles.get(expected_role)
    if role_keys is None:
        raise TrustError(f"trusted root has no role definition for {expected_role}")

    valid_key_ids: set[str] = set()
    payload = metadata.canonical_bytes()
    for signature in metadata.signatures:
        if signature.key_id not in role_keys.key_ids:
            continue
        key = root.keys[signature.key_id]
        try:
            key.public_key.verify(signature.value, payload)
        except InvalidSignature:
            continue
        valid_key_ids.add(signature.key_id)
    if len(valid_key_ids) < role_keys.threshold:
        raise TrustError(f"{expected_role} metadata did not meet signature threshold {role_keys.threshold}")


def verify_and_accept(root: TrustRoot, metadata: SignedMetadata, expected_role: str, state: MetadataState, now: datetime) -> MetadataState:
    """Verify metadata and return a new anti-rollback state after acceptance."""
    verify_metadata(root, metadata, expected_role, now)
    return state.accept(metadata)


def rotate_root(current: TrustRoot, candidate: SignedMetadata, now: datetime) -> TrustRoot:
    """Require both the old and new root thresholds for a forward root rotation."""
    verify_metadata(current, candidate, "root", now)
    candidate_root = TrustRoot.from_metadata(candidate)
    if candidate_root.version <= current.version:
        raise TrustError(f"root rollback detected: {candidate_root.version} <= {current.version}")
    verify_metadata(candidate_root, candidate, "root", now)
    return candidate_root
