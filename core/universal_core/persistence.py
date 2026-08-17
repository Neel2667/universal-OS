"""Crash-resilient local storage primitives for the host-side installation model.

JournalStore uses atomic snapshot replacement plus a previous valid snapshot.
It is not a device partition writer; it operates only in an explicitly supplied
local directory and never invokes a subprocess or network operation.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .errors import PersistenceError
from .install import InstallJournal


FORMAT_VERSION = 1


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


@dataclass(frozen=True)
class JournalSnapshot:
    sequence: int
    journal: InstallJournal

    def unsigned_dict(self) -> dict[str, Any]:
        return {"format_version": FORMAT_VERSION, "sequence": self.sequence, "journal": self.journal.to_dict()}

    def to_bytes(self) -> bytes:
        record = self.unsigned_dict()
        record["sha256"] = hashlib.sha256(_canonical_json(record)).hexdigest()
        return _canonical_json(record)

    @classmethod
    def from_bytes(cls, payload: bytes) -> "JournalSnapshot":
        try:
            raw = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PersistenceError("journal snapshot is not valid UTF-8 JSON") from exc
        if not isinstance(raw, dict):
            raise PersistenceError("journal snapshot is not an object")
        expected = {"format_version", "sequence", "journal", "sha256"}
        if set(raw) != expected or raw["format_version"] != FORMAT_VERSION:
            raise PersistenceError("journal snapshot has an unsupported format")
        sequence = raw["sequence"]
        if not isinstance(sequence, int) or sequence < 1:
            raise PersistenceError("journal snapshot has an invalid sequence")
        digest = raw["sha256"]
        unsigned = {"format_version": raw["format_version"], "sequence": sequence, "journal": raw["journal"]}
        if not isinstance(digest, str) or hashlib.sha256(_canonical_json(unsigned)).hexdigest() != digest:
            raise PersistenceError("journal snapshot integrity digest does not match")
        if not isinstance(raw["journal"], dict):
            raise PersistenceError("journal snapshot does not contain a journal object")
        try:
            journal = InstallJournal.from_dict(raw["journal"])
        except Exception as exc:
            raise PersistenceError("journal snapshot contains an invalid installation journal") from exc
        return cls(sequence, journal)


class JournalStore:
    """Atomic current/previous snapshot store with corruption fallback."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory.resolve()
        self.current_path = self.directory / "current.json"
        self.previous_path = self.directory / "previous.json"

    def _load_path(self, path: Path) -> JournalSnapshot:
        try:
            return JournalSnapshot.from_bytes(path.read_bytes())
        except FileNotFoundError as exc:
            raise PersistenceError(f"journal snapshot is missing: {path.name}") from exc

    def load(self) -> JournalSnapshot:
        current_error: Exception | None = None
        try:
            return self._load_path(self.current_path)
        except PersistenceError as exc:
            current_error = exc
        try:
            return self._load_path(self.previous_path)
        except PersistenceError as previous_error:
            raise PersistenceError(f"no valid journal snapshot: current={current_error}; previous={previous_error}") from previous_error

    def save(self, journal: InstallJournal) -> JournalSnapshot:
        previous_sequence = 0
        if self.current_path.exists():
            try:
                previous_sequence = self._load_path(self.current_path).sequence
                # Preserve an independently flushed last-known-good snapshot before replacing current.
                _atomic_write(self.previous_path, self.current_path.read_bytes())
            except PersistenceError:
                # Do not turn an already-corrupt current snapshot into the fallback.
                try:
                    previous_sequence = self._load_path(self.previous_path).sequence
                except PersistenceError:
                    previous_sequence = 0
        snapshot = JournalSnapshot(previous_sequence + 1, journal)
        _atomic_write(self.current_path, snapshot.to_bytes())
        return snapshot


@dataclass(frozen=True)
class StagedArtifact:
    target_id: str
    package_id: str
    sha256: str
    bytes: int
    path: Path


class StagingStore:
    """Digest-addressed local staging for already verified payload bytes."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory.resolve()
        self.payload_directory = self.directory / "payloads"

    def stage(self, target_id: str, package_id: str, expected_sha256: str, payload: bytes) -> StagedArtifact:
        actual = hashlib.sha256(payload).hexdigest()
        if actual != expected_sha256:
            raise PersistenceError("refusing to stage payload with mismatched digest")
        destination = self.payload_directory / actual
        if destination.exists():
            existing = destination.read_bytes()
            if hashlib.sha256(existing).hexdigest() != actual or len(existing) != len(payload):
                raise PersistenceError("existing staged payload does not match its digest-addressed path")
        else:
            _atomic_write(destination, payload)
        return StagedArtifact(target_id, package_id, actual, len(payload), destination)

    def read_verified(self, artifact: StagedArtifact) -> bytes:
        payload = artifact.path.read_bytes()
        if len(payload) != artifact.bytes or hashlib.sha256(payload).hexdigest() != artifact.sha256:
            raise PersistenceError("staged payload failed integrity recheck")
        return payload
