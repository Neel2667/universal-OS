#!/usr/bin/env python3
"""Check, without modifying the host, whether it can build UniversalOS Discovery Base.

This is deliberately a diagnostic only: it does not install packages, download a
toolchain, start QEMU, or contact a device. Its JSON output can be attached to a
build-environment issue after paths/user names are reviewed.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Callable, Iterable

MIN_RUST = (1, 85, 0)


@dataclass(frozen=True)
class Check:
    name: str
    required: bool
    found: bool
    detail: str


def parse_semver(text: str) -> tuple[int, int, int] | None:
    match = re.search(r"\b([0-9]+)\.([0-9]+)\.([0-9]+)\b", text)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def command_output(command: list[str]) -> str | None:
    try:
        return subprocess.check_output(command, stderr=subprocess.STDOUT, text=True, timeout=10).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def executable_check(name: str, *, required: bool = True, version_command: list[str] | None = None) -> Check:
    path = shutil.which(name)
    if path is None:
        return Check(name, required, False, "not found on PATH")
    if version_command is None:
        return Check(name, required, True, path)
    version = command_output(version_command)
    return Check(name, required, True, version or path)


def rust_check() -> Check:
    path = shutil.which("rustc")
    if path is None:
        return Check("rustc", True, False, f"not found; require Rust >= {'.'.join(map(str, MIN_RUST))}")
    output = command_output(["rustc", "--version"])
    version = parse_semver(output or "")
    if version is None:
        return Check("rustc", True, False, "version could not be parsed")
    if version < MIN_RUST:
        return Check("rustc", True, False, f"{output}; require >= {'.'.join(map(str, MIN_RUST))}")
    return Check("rustc", True, True, output or path)


def target_check() -> Check:
    output = command_output(["rustup", "target", "list", "--installed"])
    if output is None:
        return Check("rustup targets", True, False, "rustup unavailable; require aarch64-unknown-linux-gnu and aarch64-unknown-none")
    installed = set(output.splitlines())
    required = {"aarch64-unknown-linux-gnu", "aarch64-unknown-none"}
    missing = sorted(required - installed)
    if missing:
        return Check("rustup targets", True, False, "missing: " + ", ".join(missing))
    return Check("rustup targets", True, True, "required ARM64 targets installed")


def evaluate() -> list[Check]:
    checks = [
        rust_check(),
        executable_check("cargo", version_command=["cargo", "--version"]),
        executable_check("rustfmt", version_command=["rustfmt", "--version"]),
        executable_check("clippy-driver", version_command=["clippy-driver", "--version"]),
        target_check(),
        executable_check("bitbake", version_command=["bitbake", "--version"]),
        executable_check("qemu-system-aarch64", version_command=["qemu-system-aarch64", "--version"]),
        executable_check("git", version_command=["git", "--version"]),
        executable_check("python3", version_command=["python3", "--version"]),
    ]
    return checks


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable result")
    parser.add_argument("--strict", action="store_true", help="return non-zero when a required prerequisite is unavailable")
    args = parser.parse_args(list(argv) if argv is not None else None)
    checks = evaluate()
    ready = all(check.found for check in checks if check.required)
    if args.json:
        print(json.dumps({"ready": ready, "checks": [asdict(check) for check in checks]}, sort_keys=True))
    else:
        print("UniversalOS native build host: " + ("READY" if ready else "NOT READY"))
        for check in checks:
            status = "OK" if check.found else "MISSING"
            print(f"[{status}] {check.name}: {check.detail}")
    return 0 if ready or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
