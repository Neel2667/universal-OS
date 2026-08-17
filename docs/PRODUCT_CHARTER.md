# UniversalOS version 0.1 product charter

- **Status:** Accepted initial direction
- **Audience:** developers and contributors validating a universal, recovery-first mobile platform
- **Release type:** non-consumer Discovery Base / developer preview only

## Mission

Build one original mobile operating-system core that can serve many supported phones through small signed hardware-enablement packages, rather than shipping a separate ROM fork per model or relying on a phone vendor's update schedule.

## Version 0.1 proof

UniversalOS v0.1 succeeds when a developer can, on an approved lab profile or QEMU:

```text
use USB/offline-first installation
→ select a signed Bootstrap Capsule
→ boot Discovery Base
→ measure local non-personal hardware facts
→ select exactly one signed profile
→ transfer/fetch exact signed core and device-support artifacts
→ stage to a safe inactive/transactional target
→ boot once
→ commit after health confirmation or roll back safely
```

## Product principles

```text
One shared core, not per-device product forks
Offline-safe and account-free basic operation
Security and recovery before convenience claims
Fast, simple, workspace-first experience later
Truthful support tiers and feature matrices
No hidden data extraction or attention-maximizing dark patterns
```

## Explicit v0.1 non-goals

```text
Consumer daily-driver release
All-device compatibility promise
Locked-device or iPhone support promise
Cellular/emergency calling claim
Camera, biometrics, DRM, payments claim
Android app compatibility
AI platform
Cloud account requirement
Visual polish ahead of boot/recovery/update proof
```

## Success metrics

| Area | v0.1 success evidence |
| --- | --- |
| Universal core | Same contract/resolver behavior passes on structurally different synthetic ARM64 and ARMv7 profiles. |
| Trust | Invalid, expired, rollbacked, mismatched, unsigned, and tampered metadata/artifacts are rejected. |
| Recovery | Simulated interruption/failed-health paths preserve known-good target; physical recovery proof is later mandatory. |
| Privacy | No profile, log, or catalog accepts unique device identifiers or account identity. |
| Portability | New device is admitted through adapter/profile/provenance/recovery evidence rather than core device-name conditionals. |
| Developer clarity | Fresh environment can run the reference tests and read the handoff/build path. |

## Exit criteria for developer preview planning

- Native Rust/Yocto/QEMU Discovery Base build works reproducibly.
- QEMU demonstrates installer → profile → transfer → stage → health/rollback path.
- At least one physical lab adapter has independently tested offline recovery.
- Test/release provenance and signing process pass review.
- Known limitations are published before any image distribution.
