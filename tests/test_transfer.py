from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.artifacts import TargetDescriptor
from universal_core.errors import PersistenceError, TrustError
from universal_core.transfer import ResumableTransferStore, TransferManifest


def build_manifest(payload: bytes, *, artifact_kind: str = "payload", transfer_id: str = "test-transfer-001") -> tuple[TransferManifest, TargetDescriptor, list[bytes]]:
    chunk_size = 4096
    chunks = [payload[index : index + chunk_size] for index in range(0, len(payload), chunk_size)]
    digest = hashlib.sha256(payload).hexdigest()
    descriptor = TargetDescriptor(
        "uos.test.target@0.1.0",
        "uos.test.package",
        "f" * 64 if artifact_kind == "payload" else digest,
        1 if artifact_kind == "payload" else len(payload),
        digest if artifact_kind == "payload" else "f" * 64,
        len(payload) if artifact_kind == "payload" else 1,
    )
    raw = {
        "schema_version": 1,
        "transfer_id": transfer_id,
        "target_id": descriptor.target_id,
        "artifact_kind": artifact_kind,
        "sha256": digest,
        "bytes": len(payload),
        "chunk_bytes": chunk_size,
        "chunk_sha256": [hashlib.sha256(chunk).hexdigest() for chunk in chunks],
    }
    return TransferManifest.from_dict(raw), descriptor, chunks


class TransferTests(unittest.TestCase):
    def test_transfer_resumes_and_finalizes_verified_payload(self) -> None:
        payload = b"A" * 4096 + b"B" * 4096 + b"C" * 17
        manifest, descriptor, chunks = build_manifest(payload)
        with tempfile.TemporaryDirectory() as directory:
            first = ResumableTransferStore(Path(directory), manifest, descriptor)
            first.receive_chunk(1, chunks[1])
            restarted = ResumableTransferStore(Path(directory), manifest, descriptor)
            self.assertEqual(restarted.missing_chunks, (0, 2))
            restarted.receive_chunk(0, chunks[0])
            restarted.receive_chunk(2, chunks[2])
            complete = restarted.finalize()
            self.assertEqual(complete.path.read_bytes(), payload)
            self.assertEqual(restarted.missing_chunks, ())

    def test_wrong_chunk_or_wrong_descriptor_is_rejected(self) -> None:
        payload = b"Z" * 4096
        manifest, descriptor, chunks = build_manifest(payload)
        with tempfile.TemporaryDirectory() as directory:
            transfer = ResumableTransferStore(Path(directory), manifest, descriptor)
            with self.assertRaises(TrustError):
                transfer.receive_chunk(0, b"Y" * 4096)
        wrong = TargetDescriptor(descriptor.target_id, descriptor.package_id, descriptor.manifest_sha256, descriptor.manifest_bytes, "0" * 64, descriptor.payload_bytes)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(TrustError):
                ResumableTransferStore(Path(directory), manifest, wrong)

    def test_finalize_requires_every_chunk(self) -> None:
        payload = b"A" * 4096 + b"B" * 4096
        manifest, descriptor, chunks = build_manifest(payload)
        with tempfile.TemporaryDirectory() as directory:
            transfer = ResumableTransferStore(Path(directory), manifest, descriptor)
            transfer.receive_chunk(0, chunks[0])
            with self.assertRaises(PersistenceError):
                transfer.finalize()

    def test_transfer_manifest_never_authorizes_unknown_target(self) -> None:
        payload = b"A" * 4096
        manifest, descriptor, _ = build_manifest(payload)
        altered = TargetDescriptor("different-target", descriptor.package_id, descriptor.manifest_sha256, descriptor.manifest_bytes, descriptor.payload_sha256, descriptor.payload_bytes)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(TrustError):
                ResumableTransferStore(Path(directory), manifest, altered)


if __name__ == "__main__":
    unittest.main()
