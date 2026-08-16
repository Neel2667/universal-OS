# UniversalOS Discovery Base build strategy

## Objective

Produce the first **bootable, immutable, reproducible UniversalOS Discovery Base** for QEMU ARM64 before attempting physical hardware. The image is a recovery/discovery environment, not a consumer ROM.

## Selected stack

```text
Image factory:       Yocto / OpenEmbedded
Native trusted code: Rust
Service supervision: systemd
IPC transport:       local Unix socket + peer credentials
Target first:        QEMU `virt` ARM64
Hardware later:      signed Bootstrap Capsule adapters
```

## Source layout to introduce

```text
meta-universalos/
  conf/
    layer.conf
    distro/universalos.conf
    machine/universalos-qemuarm64.conf
  recipes-core/
    uos-discovery-base/
    uos-services/
  recipes-security/
    uos-trust/
  recipes-support/
    uos-recovery-tools/

native/
  Cargo.toml
  crates/
    uos-contracts/
    uos-profile-service/
    uos-update-service/
    uos-health-service/
    uos-recovery-service/
    uos-ipc/
```

This structure is intentionally not committed until the exact Yocto release and Rust toolchain can be pinned and built in a clean environment. An untested build layer is worse than no build layer.

## Image boundaries

| Area | Mutable? | Contents |
| --- | --- | --- |
| Bootstrap Capsule | profile-controlled | kernel, device tree, essential early modules/firmware, recovery bridge |
| Discovery Base root | immutable | Rust services, system manager, verified local IPC, minimum diagnostics |
| State partition | controlled writable | update journal, verified staging, recovery records, no private keys |
| User-data partition | later product phase | user files/apps; excluded from Discovery Base proof |

## Build stages

### B0 — Native workspace and reproducibility

- Pin Rust compiler, Cargo, target triples, linker, and source checksums.
- Create a Rust workspace from the tested Python contracts.
- Keep Python test vectors as a behavior oracle during migration.
- Cross-compile a minimal ARM64 static service binary.

### B1 — QEMU ARM64 Discovery Base

- Pin Yocto/OE release and layer revisions.
- Build minimal ARM64 image with systemd, Unix socket policy, Rust services, and a serial console.
- Boot on QEMU `virt` hardware.
- Prove no required cloud/network path exists for boot, profile reporting, journal read, or recovery status.

### B2 — Verified update laboratory

- Add signed test metadata/targets generated with non-production keys outside Git.
- Stage a harmless test payload into a QEMU state image.
- Simulate interruption/corruption/health failure and confirm rollback.
- Produce image manifest, SBOM, and reproducible build comparison.

### B3 — Hardware adapter admission

- Implement an approved Bootstrap Capsule for a named disposable lab device.
- Validate restore/recovery before writing a UniversalOS system partition.
- Keep vendor/mainline hardware code out of UniversalOS core crates.

## Non-goals for the first image

```text
No Android app compatibility
No browser
No app store
No GUI shell beyond required recovery/diagnostic display
No cloud account
No AI runtime
No telephony/camera claim
No physical device flash
```

## Why QEMU first

QEMU gives a reproducible ARM64 environment for testing image layout, service permissions, signed metadata, journal durability, rollback behavior, and serial-console recovery without risking a phone. It does not validate phone radios, GPU, camera, vendor firmware, or actual bootloader behavior; those need a later hardware adapter.
