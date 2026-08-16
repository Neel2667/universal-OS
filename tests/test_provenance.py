from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from validate_provenance import ProvenanceError, ProvenanceRecord


def load(name: str) -> dict:
    return json.loads((ROOT / f"testdata/provenance/{name}.json").read_text(encoding="utf-8"))


class ProvenanceTests(unittest.TestCase):
    def test_open_source_and_user_extraction_records_parse(self) -> None:
        source = ProvenanceRecord.from_dict(load("open-source-contracts"))
        firmware = ProvenanceRecord.from_dict(load("restricted-firmware-example"))
        self.assertEqual(source.kind, "source")
        self.assertEqual(firmware.redistribution, "user-extraction-only")

    def test_unknown_or_personal_field_is_rejected(self) -> None:
        raw = load("restricted-firmware-example")
        raw["device_serial"] = "must-not-be-in-inventory"
        with self.assertRaises(ProvenanceError):
            ProvenanceRecord.from_dict(raw)

    def test_unapproved_redistributable_firmware_is_rejected(self) -> None:
        raw = load("restricted-firmware-example")
        raw["redistribution"] = "allowed"
        raw["review"]["state"] = "unreviewed"
        with self.assertRaises(ProvenanceError):
            ProvenanceRecord.from_dict(raw)


if __name__ == "__main__":
    unittest.main()
