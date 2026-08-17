# UniversalOS project handoff

> **Read this first when taking over the project in a new chat, terminal, or agent session.** This document is the compact operating context; linked documents contain the detailed evidence.

- **Repository:** `Neel2667/universal-OS`
- **Active branch:** `arena/01a00b34-universal-os`
- **Active pull request:** [#34 — UniversalOS foundation and delivery backlog](https://github.com/Neel2667/universal-OS/pull/34)
- **Date updated:** 2026-08-16
- **Status:** portable-core/security/transfer reference implementation; no bootable Discovery Base image yet.

## Mission

Build **one UniversalOS product core**, not a separately forked ROM for every phone.

```text
Small signed Bootstrap Capsule per approved board/SoC family
  → shared UniversalOS Discovery Base
  → local hardware measurement
  → signed exact profile selection
  → signed driver/device-support + core selection
  → safe staged install
  → health confirmation or rollback
```

The cloud distributes candidates; the local device verifier makes the security and compatibility decision.

## Product decisions already made

| Decision | Current choice |
| --- | --- |
| Product structure | One portable UniversalOS Core plus small signed device-enablement/Bootstrap Capsule packages. |
| Initial hardware role | Xiaomi Mi A2 is a **lab candidate only**, not a UniversalOS product fork or public supported device. It is unlocked and currently runs Ubuntu Touch; do not modify it without recovery proof. |
| Main OS language | Rust-first trusted core. Python is the executable reference model/test oracle only. C/C++ is isolated to unavoidable kernel/vendor/graphics interfaces. |
| System/image base | Custom Yocto/OpenEmbedded Discovery Base image with Linux hardware adapters, systemd supervision, immutable root direction, local peer-authenticated IPC. See ADR-002. |
| First-install connectivity | USB Universal Installer first; phone does not need Wi-Fi/cellular before boot. Offline transfer is required; Wi-Fi becomes optional after compatible local support exists. |
| Privacy/account | Account-free basic operation; diagnostics/crash upload are opt-in; no hidden telemetry. See ADR-005. |
| Device lifecycle | Profiled/lab/verified/maintained/retired tiers require evidence; see ADR-007. |
| AI | Explicitly excluded from current core scope. Do not reintroduce it unless the owner reopens the decision. |
| UI prototype | Static interactive workspace/update/privacy/recovery prototype is available under `prototype/`; it is visual only and not connected to hardware services. |
| Device claims | No phone is supported yet. No physical device has been flashed, rebooted, or modified by this project. |

## Read in this order

1. [README](../README.md)
2. [Signed Bootstrap Capsule catalog](SIGNED_BOOTSTRAP_CATALOG.md)
3. [Universality model](UNIVERSALITY_MODEL.md)
4. [Accepted ADR-002](adr/ADR-002-system-and-hardware-base.md)
5. [Bootstrap-to-full-system flow](BOOTSTRAP_DISCOVERY_FLOW.md)
6. [Connectivity bootstrap](CONNECTIVITY_BOOTSTRAP.md)
7. [Universal Installer rehearsal](INSTALLER_REHEARSAL.md)
8. [Product charter](PRODUCT_CHARTER.md)
9. [Privacy/account decision](adr/ADR-005-privacy-diagnostics-account-policy.md)
10. [Device lifecycle decision](adr/ADR-007-device-lifecycle-policy.md)
11. [Experience journeys](UX_JOURNEYS.md) and [performance/accessibility budgets](PERFORMANCE_ACCESSIBILITY.md)
12. [UI foundation](UI_FOUNDATION.md), [Stitch prompt pack](STITCH_PROMPT_PACK.md), and [static prototype](../prototype/README.md)
13. [Managed workstreams](WORKSTREAMS.md)
14. [Project plan](PROJECT_PLAN.md)
15. [Risk register](RISK_REGISTER.md) and [threat model](THREAT_MODEL.md)
16. [Definition of done](DEFINITION_OF_DONE.md)

## What exists in code today

The Python reference model implements and tests:

```text
hardware discovery records
Bootstrap Capsule selection
signed Bootstrap Capsule catalog
signed exact hardware profiles
package compatibility resolver
Ed25519 root/threshold/rotation/expiry/rollback metadata checks
signed target → manifest → payload binding
disposable signed test repository
preflight, staging, transaction journal, health, rollback model
capability-gated local service protocol
Linux Unix-domain peer-authenticated IPC reference
USB/offline chunked resumable verified transfer model
end-to-end installer rehearsal chaining signed bootstrap/profile/targets/transfer
mirror/offline bundle, fault matrix, SBOM, device-enablement, health-attestation, audit, release-gate, bootstrap-adapter, recovery-proof, package-admission, storage-layout, device-matrix, reproducible-build, USB Installer dry-run, and network-provisioning reference tooling
source/firmware/model provenance metadata validation
```

Important: this is host-side reference behavior. It is **not** a kernel, boot image, USB gadget driver, fastboot client, downloader, flasher, or production OTA service.

## Current user-facing installation model

```text
Computer Universal Installer downloads signed artifacts
  → approved bootloader/recovery path transfers minimal Bootstrap Capsule
  → Discovery Base boots on phone
  → local facts choose one signed profile
  → computer USB transfer / offline bundle / later Wi-Fi supplies artifacts
  → phone verifies and stages every artifact itself
```

Do not design a network-only first boot. The selected local Bootstrap Capsule supplies the minimum boot/storage/USB path and, where applicable, Wi-Fi support.

## Current blockers

```text
Rust/Cargo/rustfmt/clippy unavailable on Arena build host
BitBake/Yocto unavailable on Arena build host
QEMU ARM64 unavailable on Arena build host
External Rust/Debian toolchain endpoints were unavailable from this host
```

Run the non-destructive diagnostic:

```sh
python3 tools/check_native_build_host.py
```

Do not claim a native Discovery Base build until this host/toolchain problem is resolved and a clean build has passed.

## Current critical path

1. Establish pinned Rust + Yocto + QEMU ARM64 build environment.
2. Create native Rust workspace and port the Python contract behavior into Rust tests.
3. Create `meta-universalos` Yocto layer and QEMU ARM64 Discovery Base image.
4. Boot QEMU image; prove native local service/IPC/recovery status.
5. Integrate signed test repository and transfer model in QEMU.
6. Prove staged update, interruption, failed health, and rollback in QEMU.
7. Only then begin controlled real-device recovery proof.
8. UI/app-runtime work remains after system image/recovery/update proof.

## Commands to validate the current reference model

```sh
python3 -m venv /tmp/universalos-venv
. /tmp/universalos-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python tools/validate_contracts.py
python tools/validate_provenance.py
python -m unittest discover -s tests -v
python tools/check_native_build_host.py
```

## GitHub usage

- GitHub Issues are the planned work source of truth; initial backlog maps 33 issues to seven milestones.
- [Initial backlog](INITIAL_BACKLOG.md) and [workstreams](WORKSTREAMS.md) are the repository-side navigation source.
- Security reports use [SECURITY.md](../SECURITY.md), never public exploit issues.
- The current PR is open; `main` has not been updated. New work must remain on `arena/01a00b34-universal-os` and be pushed there.

## Non-negotiable safety rules

```text
Never put private keys, vendor firmware, extracted partitions, user data, IMEI, serial numbers, or MAC addresses in Git.
Never treat cloud/USB transport as a trust root.
Never overwrite the only known-good boot target.
Never claim untested hardware/cellular/recovery support.
Never flash the Mi A2 until real restore/recovery gates are approved.
Never reintroduce local AI into core scope without owner approval.
```
