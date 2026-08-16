from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.contracts import HardwareProfile
from universal_core.errors import PersistenceError
from universal_core.install import InstallJournal
from universal_core.persistence import JournalStore, StagingStore


def profile() -> HardwareProfile:
    return HardwareProfile.from_dict(json.loads((ROOT / "testdata/profiles/synthetic-orion-arm64.json").read_text(encoding="utf-8")))


class PersistenceTests(unittest.TestCase):
    def test_journal_round_trip_and_sequence_increment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JournalStore(Path(directory))
            first = store.save(InstallJournal.begin(profile(), "a").metadata_verified())
            second_journal = first.journal.artifacts_verified(["uos.core"]).stage()
            second = store.save(second_journal)
            loaded = store.load()
            self.assertEqual(first.sequence, 1)
            self.assertEqual(second.sequence, 2)
            self.assertEqual(loaded.sequence, 2)
            self.assertEqual(loaded.journal, second_journal)

    def test_corrupt_current_snapshot_falls_back_to_previous_valid_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JournalStore(Path(directory))
            first = store.save(InstallJournal.begin(profile(), "a").metadata_verified())
            store.save(first.journal.artifacts_verified(["uos.core"]))
            store.current_path.write_bytes(b"corrupt")
            loaded = store.load()
            self.assertEqual(loaded.sequence, 1)
            self.assertEqual(loaded.journal, first.journal)

    def test_staging_store_rechecks_digest_addressed_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = StagingStore(Path(directory))
            payload = b"universal staged artifact"
            import hashlib

            artifact = store.stage("target-1", "uos.core", hashlib.sha256(payload).hexdigest(), payload)
            self.assertEqual(store.read_verified(artifact), payload)
            artifact.path.write_bytes(b"tampered")
            with self.assertRaises(PersistenceError):
                store.read_verified(artifact)


if __name__ == "__main__":
    unittest.main()
