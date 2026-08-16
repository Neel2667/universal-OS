from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from check_native_build_host import MIN_RUST, parse_semver


class NativeHostToolTests(unittest.TestCase):
    def test_parses_rust_and_cargo_style_versions(self) -> None:
        self.assertEqual(parse_semver("rustc 1.85.0 (4d91de4e4 2025-02-17)"), (1, 85, 0))
        self.assertEqual(parse_semver("cargo 1.90.0"), (1, 90, 0))

    def test_rejects_unparseable_versions(self) -> None:
        self.assertIsNone(parse_semver("not installed"))
        self.assertIsNone(parse_semver("rustc 1.85"))

    def test_native_workspace_requires_edition_2024_capable_rust(self) -> None:
        self.assertGreaterEqual(MIN_RUST, (1, 85, 0))


if __name__ == "__main__":
    unittest.main()
