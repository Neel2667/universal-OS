#!/usr/bin/env python3
"""CLI wrapper for a non-production UniversalOS signed test repository."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from test_repository import TestRepositoryError, generate_test_repository, verify_test_repository


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="empty directory outside this source checkout")
    parser.add_argument("--i-understand-test-keys", action="store_true", help="required: output contains disposable test-only private keys")
    args = parser.parse_args()
    try:
        report = generate_test_repository(args.destination, acknowledge_test_keys=args.i_understand_test_keys)
        verified = verify_test_repository(report.path, now=datetime(2026, 8, 16, tzinfo=timezone.utc))
    except TestRepositoryError as exc:
        parser.error(str(exc))
    print(f"Created and verified TEST-ONLY repository at {verified.path} with {verified.target_count} targets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
