# ADR-002 — Select the initial system and hardware foundation

- **Status:** Accepted for the Discovery Base implementation
- **Date:** 2026-08-16
- **Related issue:** [#4](https://github.com/Neel2667/universal-OS/issues/4)
- **Supersedes:** no prior decision

## Context

UniversalOS must be visibly and architecturally different from Android and ordinary Linux distributions while still reaching real phone hardware. A new kernel and driver stack for every historical SoC would make the project unable to meet its portability goal. Conversely, an Android UI/framework fork would not create a distinct operating system.

The project needs a build foundation for an immutable Discovery Base, a safe device-enablement boundary, native local services, and reproducible images across ARM64/ARMv7/x86_64/RISC-V test profiles.

## Options considered

| Option | Benefits | Costs / risks | Decision |
| --- | --- | --- | --- |
| Fork AOSP as the whole platform | Broad Android hardware starting point and mature tooling | Android framework/UI/update assumptions leak into product; high vendor debt; weak differentiation | Rejected as primary platform |
| Fork a general Linux mobile distribution | Existing mobile userspace and some device ports | Inherits another product's UX/service model; uneven hardware support | Rejected as primary platform |
| New kernel and all-new drivers | Maximum technical independence | Cannot support broad existing phone hardware in a realistic timeframe | Rejected for initial product |
| **Rust-first UniversalOS core on Linux hardware adapters, built as a custom Yocto/OE image** | New system identity above the kernel; reusable hardware capsules; immutable/reproducible image factory; long-term multi-board layers | Requires careful vendor-kernel compatibility work and a steeper initial build setup | **Accepted** |

## Decision

UniversalOS will use the following foundation:

```text
Hardware / kernel boundary
  → Linux kernel supplied by a signed Bootstrap Capsule
     - mainline/close-to-mainline backend where viable
     - controlled Android/vendor-kernel compatibility backend where required

Discovery Base
  → minimal immutable Linux userspace image built through Yocto/OpenEmbedded
  → Rust-first UniversalOS services
  → systemd service supervision and local peer-authenticated IPC
  → no Android framework, launcher, package manager, or Google service dependency

UniversalOS Core
  → Rust for trusted services: discovery, profile, update, trust, recovery, health, IPC
  → narrow C FFI only for kernel/vendor/graphics interfaces that cannot yet be replaced
  → Python reference implementation retained only as test oracle/tooling

Application and UI layers
  → intentionally deferred until Discovery Base/recovery/update proof exists
```

Yocto/OpenEmbedded is the production image factory. It constructs the target userspace, initramfs, toolchain, filesystem image, package inputs, license/SBOM data, and architecture-specific artifacts from versioned recipes/layers. It is **not** the UniversalOS product experience and it does not replace the UniversalOS updater.

## Consequences

### Positive

- UniversalOS keeps one product core while device support is isolated in Bootstrap Capsules and profile packages.
- Rust makes new trusted components memory-safe by default while keeping native performance and small deployment options.
- A Yocto layer can build immutable Discovery Base images for emulation and later hardware profiles from a declared source graph.
- Existing Android/Linux hardware enablement can be reused only behind a narrow adapter boundary, not copied into the system UI/app model.
- Mainline-capable devices can move toward shared SoC/kernel support over time.

### Costs and controls

- A vendor kernel remains a blocker for some old devices; the project must publish the security/support tier honestly.
- Rust does not remove the need for C in existing Linux kernels and vendor drivers. Unsafe FFI must be restricted, reviewed, and tested.
- Yocto has a significant learning/build-resource cost. The initial image must be intentionally minimal and reproducible, not a generic desktop distribution.
- systemd is selected for supervised services, socket activation, and identity boundaries; the initial service set remains minimal.
- Native UniversalOS image code cannot be declared complete until cross compilation, QEMU boot, SBOM, image signing, and recovery tests pass.

## Initial image composition

```text
UOS Discovery Base image
  kernel / device tree / early modules         ← Bootstrap Capsule boundary
  initramfs                                   ← discovery, recovery transport, hardware facts
  immutable root userspace                     ← Yocto/OE image
  systemd + UniversalOS Rust services          ← profile, trust, update, health, recovery IPC
  writable state partition                     ← journal, staged verified artifacts, user-approved logs
  no normal app runtime, browser, cloud agent, or Android framework
```

## Evidence and implementation gates

- [ ] Pin a Rust toolchain and create the native workspace; Python prototype behavior becomes test vectors.
- [ ] Create `meta-universalos` Yocto/OE layer with a QEMU ARM64 Discovery Base image recipe.
- [ ] Boot the image in QEMU and prove local peer-authenticated service status/recovery calls.
- [ ] Generate an SBOM/source-license record for the image.
- [ ] Define immutable root/state partition layout and image signing path.
- [ ] Prove recovery and update rollback in QEMU before device integration.
- [ ] Add a real device only after the target's Bootstrap Capsule, source provenance, and restore path pass review.

## Sources consulted

- [Android Generic Kernel Image overview](https://source.android.com/docs/core/architecture/kernel/generic-kernel-image) — generic core kernel versus vendor modules/KMI separation.
- [postmarketOS device categorization](https://docs.postmarketos.org/pmaports/main/packaging/device-categorization.html) — why maintainable mainline/close-to-mainline support must be separated from downstream vendor-kernel ports.
- [Buildroot manual](https://buildroot.org/downloads/manual/manual.html) — comparison point for small complete embedded images; not selected as the production image factory.
- [Yocto Project technical overview](https://www.yoctoproject.org/development/technical-overview/) — layers/recipes, custom image construction, test/security/license/SBOM support.
- [Embedded Rust `no_std` overview](https://docs.rust-embedded.org/book/intro/no-std.html) — bootstrapping constraints and the `core`-only boundary for minimal code.
