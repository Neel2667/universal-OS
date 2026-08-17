"""Resumable USB/offline transfer model bound to verified target metadata.

This module is transport-neutral: a USB gadget, recovery file transfer, offline
bundle reader, or host relay may supply chunks. It never treats the transfer
manifest as authorization. Before chunks are accepted, the manifest must match
an already verified signed target descriptor; after completion, full bytes are
hashed again against that descriptor.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .artifacts import TargetDescriptor
from .errors import PersistenceError, TrustError


TRANSFER_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,120}$")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


@dataclass(frozen=True)
class TransferManifest:
    transfer_id: str
    target_id: str
    artifact_kind: str
    sha256: str
    bytes: int
    chunk_bytes: int
    chunk_sha256: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "TransferManifest":
        required = {"schema_version", "transfer_id", "target_id", "artifact_kind", "sha256", "bytes", "chunk_bytes", "chunk_sha256"}
        if set(raw) != required or raw.get("schema_version") != 1:
            raise TrustError("invalid transfer manifest envelope")
        transfer_id = raw["transfer_id"]
        target_id = raw["target_id"]
        artifact_kind = raw["artifact_kind"]
        digest = raw["sha256"]
        size = raw["bytes"]
        chunk_size = raw["chunk_bytes"]
        chunks = raw["chunk_sha256"]
        if not isinstance(transfer_id, str) or not TRANSFER_ID.fullmatch(transfer_id):
            raise TrustError("invalid transfer id")
        if not isinstance(target_id, str) or not target_id:
            raise TrustError("invalid transfer target id")
        if artifact_kind not in {"manifest", "payload"}:
            raise TrustError("invalid transfer artifact kind")
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise TrustError("invalid transfer digest")
        if not isinstance(size, int) or size < 1:
            raise TrustError("invalid transfer byte count")
        if not isinstance(chunk_size, int) or not 4096 <= chunk_size <= 4 * 1024 * 1024:
            raise TrustError("invalid transfer chunk size")
        if not isinstance(chunks, list) or not chunks or any(not isinstance(item, str) or not re.fullmatch(r"[a-f0-9]{64}", item) for item in chunks):
            raise TrustError("invalid transfer chunk digests")
        expected_count = (size + chunk_size - 1) // chunk_size
        if len(chunks) != expected_count:
            raise TrustError("transfer chunk count does not match byte count")
        return cls(transfer_id, target_id, artifact_kind, digest, size, chunk_size, tuple(chunks))

    def bind(self, descriptor: TargetDescriptor) -> None:
        if self.target_id != descriptor.target_id:
            raise TrustError("transfer target is absent or mismatched in verified target metadata")
        expected_digest, expected_size = (
            (descriptor.manifest_sha256, descriptor.manifest_bytes)
            if self.artifact_kind == "manifest"
            else (descriptor.payload_sha256, descriptor.payload_bytes)
        )
        if self.sha256 != expected_digest or self.bytes != expected_size:
            raise TrustError("transfer manifest does not match verified target artifact identity")

    def chunk_length(self, index: int) -> int:
        if index < 0 or index >= len(self.chunk_sha256):
            raise PersistenceError("transfer chunk index is out of range")
        start = index * self.chunk_bytes
        return min(self.chunk_bytes, self.bytes - start)


@dataclass(frozen=True)
class TransferJournal:
    manifest: TransferManifest
    received: frozenset[int]
    completed: bool

    def to_bytes(self) -> bytes:
        unsigned = {
            "schema_version": 1,
            "transfer_id": self.manifest.transfer_id,
            "target_id": self.manifest.target_id,
            "artifact_kind": self.manifest.artifact_kind,
            "sha256": self.manifest.sha256,
            "bytes": self.manifest.bytes,
            "chunk_bytes": self.manifest.chunk_bytes,
            "chunk_sha256": list(self.manifest.chunk_sha256),
            "received": sorted(self.received),
            "completed": self.completed,
        }
        unsigned["journal_sha256"] = _sha256(_canonical(unsigned))
        return _canonical(unsigned)

    @classmethod
    def from_bytes(cls, data: bytes) -> "TransferJournal":
        try:
            raw = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PersistenceError("transfer journal is not valid JSON") from exc
        if not isinstance(raw, dict) or "journal_sha256" not in raw:
            raise PersistenceError("transfer journal envelope is invalid")
        digest = raw.pop("journal_sha256")
        if not isinstance(digest, str) or _sha256(_canonical(raw)) != digest:
            raise PersistenceError("transfer journal integrity digest does not match")
        received = raw.pop("received", None)
        completed = raw.pop("completed", None)
        raw["schema_version"] = raw.get("schema_version")
        manifest = TransferManifest.from_dict(raw)
        if not isinstance(received, list) or any(not isinstance(index, int) or index < 0 or index >= len(manifest.chunk_sha256) for index in received):
            raise PersistenceError("transfer journal received index set is invalid")
        if not isinstance(completed, bool):
            raise PersistenceError("transfer journal completion state is invalid")
        return cls(manifest, frozenset(received), completed)


@dataclass(frozen=True)
class CompletedTransfer:
    manifest: TransferManifest
    path: Path


class ResumableTransferStore:
    """File-backed transfer store for a future Discovery Base transport adapter."""

    def __init__(self, directory: Path, manifest: TransferManifest, descriptor: TargetDescriptor) -> None:
        manifest.bind(descriptor)
        self.directory = directory.resolve()
        self.manifest = manifest
        self.descriptor = descriptor
        self.journal_path = self.directory / "journals" / f"{manifest.transfer_id}.json"
        self.partial_path = self.directory / "partial" / f"{manifest.transfer_id}.part"
        self.complete_path = self.directory / "complete" / manifest.sha256
        self.journal = self._load_or_create()

    def _load_or_create(self) -> TransferJournal:
        if self.journal_path.exists():
            journal = TransferJournal.from_bytes(self.journal_path.read_bytes())
            if journal.manifest != self.manifest:
                raise PersistenceError("existing transfer id has different manifest identity")
            return journal
        self.partial_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with self.partial_path.open("wb") as handle:
            handle.truncate(self.manifest.bytes)
            handle.flush()
            os.fsync(handle.fileno())
        journal = TransferJournal(self.manifest, frozenset(), False)
        _atomic_write(self.journal_path, journal.to_bytes())
        return journal

    @property
    def missing_chunks(self) -> tuple[int, ...]:
        return tuple(index for index in range(len(self.manifest.chunk_sha256)) if index not in self.journal.received)

    def receive_chunk(self, index: int, data: bytes) -> None:
        if self.journal.completed:
            raise PersistenceError("cannot add chunk to completed transfer")
        expected_length = self.manifest.chunk_length(index)
        if len(data) != expected_length:
            raise PersistenceError("transfer chunk has incorrect length")
        if _sha256(data) != self.manifest.chunk_sha256[index]:
            raise TrustError("transfer chunk digest does not match")
        with self.partial_path.open("r+b") as handle:
            handle.seek(index * self.manifest.chunk_bytes)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        self.journal = TransferJournal(self.manifest, self.journal.received | {index}, False)
        _atomic_write(self.journal_path, self.journal.to_bytes())

    def finalize(self) -> CompletedTransfer:
        if self.missing_chunks:
            raise PersistenceError("cannot finalize transfer with missing chunks")
        payload = self.partial_path.read_bytes()
        if len(payload) != self.manifest.bytes or _sha256(payload) != self.manifest.sha256:
            raise TrustError("completed transfer does not match verified artifact digest")
        self.complete_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.replace(self.partial_path, self.complete_path)
        self.journal = TransferJournal(self.manifest, self.journal.received, True)
        _atomic_write(self.journal_path, self.journal.to_bytes())
        return CompletedTransfer(self.manifest, self.complete_path)
