from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from test_repository import TestRepositoryError, generate_test_repository, verify_test_repository

NOW = datetime(2026, 8, 16, tzinfo=timezone.utc)


class TestRepositoryTests(unittest.TestCase):
    def test_explicit_test_only_repository_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "repository"
            generated = generate_test_repository(destination, acknowledge_test_keys=True)
            verified = verify_test_repository(destination, now=NOW)
            self.assertEqual(generated.target_count, 3)
            self.assertEqual(verified.target_count, 3)
            self.assertEqual((destination / "keys" / "test-root-ed25519.raw").stat().st_mode & 0o777, 0o600)

    def test_generation_requires_explicit_test_key_acknowledgement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(TestRepositoryError, "explicit acknowledgement"):
                generate_test_repository(Path(directory) / "repository", acknowledge_test_keys=False)

    def test_tampered_artifact_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "repository"
            generate_test_repository(destination, acknowledge_test_keys=True)
            artifact = next((destination / "artifacts").glob("*.bin"))
            artifact.write_bytes(b"tampered")
            with self.assertRaises(Exception):
                verify_test_repository(destination, now=NOW)


if __name__ == "__main__":
    unittest.main()
