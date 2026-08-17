# Native Discovery Base build environment

## Purpose

The UniversalOS production path moves the trusted core from the Python reference model to a Rust-first native workspace and a Yocto/OpenEmbedded QEMU ARM64 image. Native code and images must not be added until they can be built and tested in a pinned clean environment.

## Required host tools

```text
Rust compiler      >= 1.85.0 (Edition 2024 capable)
Cargo              matching Rust toolchain
rustfmt + clippy   matching Rust toolchain
Rust ARM64 targets aarch64-unknown-linux-gnu and aarch64-unknown-none
BitBake / Yocto    pinned release checkout, not system tip
QEMU ARM64         qemu-system-aarch64
Git + Python 3     source and supporting build tools
```

The toolchain version and Yocto layer revisions will be committed only after a clean build host resolves and verifies them. Do not use an unpinned `stable` compiler channel for release artifacts.

## Non-destructive host check

```sh
python3 tools/check_native_build_host.py
python3 tools/check_native_build_host.py --json
python3 tools/check_native_build_host.py --strict
```

The checker only reports missing tools. It never installs packages, downloads code, changes PATH, launches QEMU, or contacts a device.

## Option 1 container activation

A Dev Container definition now exists at `.devcontainer/devcontainer.json`. See [Option 1 — Arena native container activation](../native/environment/ARENA_OPTION1.md).

## Selected provisioning target

The project owner selected **Arena** as the target native build environment. See [Arena native build provisioning request](../native/environment/PROVISIONING.md).

## Current Arena host observation

At the time this document was added, the sandbox did not expose `rustc`, Cargo, BitBake, or QEMU ARM64. Direct toolchain/package download endpoints were unavailable from this host. That blocks a truthful native build run here, but it does not alter repository design or the Python reference test suite.

The next native commit begins only after a clean toolchain is available; it will contain a minimal Rust workspace, `no_std` compatibility crate, host service crate, pinned targets, and reproducible build commands.
