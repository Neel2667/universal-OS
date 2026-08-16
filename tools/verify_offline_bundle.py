#!/usr/bin/env python3
"""Verify a downloaded UniversalOS test-only offline bundle without network."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
from test_repository import TestRepositoryError, verify_test_repository

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    try:
        report = verify_test_repository(args.bundle, now=datetime(2026, 8, 16, tzinfo=timezone.utc))
    except TestRepositoryError as exc:
        parser.error(str(exc))
    print(f"Verified TEST-ONLY offline bundle with {report.target_count} target(s): {report.path}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
