# Bootstrap, discovery, and full-system delivery flow

## The intended UniversalOS experience

This document captures the product flow:

> A user starts with a small UniversalOS base. It identifies the phone's hardware, securely obtains the exact matching support package, then installs the full UniversalOS system. After installation, core and device-support updates continue for every compatible profile without waiting for the original phone vendor.

The system must feel like one OS, one installer, one update experience—not a different ROM project per phone.

## The necessary bootstrapping refinement

A phone cannot execute a completely hardware-agnostic image before it has compatible code for its boot ROM/bootloader, CPU, storage, display or USB path, and initial network route. Therefore the first small image is called the **Discovery Base**. It consists of:

- a portable UniversalOS discovery/recovery environment; and
- the smallest required **Bootstrap Capsule** for the detected board/SoC family.

The capsule is not a device-specific product fork. It is a limited, signed, replaceable compatibility adapter: boot configuration, kernel/device tree, mandatory early modules/firmware, and recovery transport. The UniversalOS services and UI are shared.

For known unlockable devices, the Universal Installer can obtain preliminary non-personal facts through the permitted USB bootloader/recovery protocol, choose the matching capsule, and flash only that minimal discovery base. For an already bootable profile, the local discovery base makes the final decision from measured hardware facts.

## End-to-end state flow

```text
[1] Universal Installer / local recovery media
      │ reads allowed preliminary board/boot facts
      ▼
[2] Signed Bootstrap Capsule selected
      │ minimal board-compatible boot path only
      ▼
[3] Discovery Base boots on the phone
      │ shared UniversalOS discovery/recovery services
      ▼
[4] Local Hardware Discovery
      │ board · SoC · architecture · partition model · kernel ABI
      │ capabilities · required firmware class · boot/rollback constraints
      ▼
[5] Signed Compatibility Registry
      │ mirror may suggest; local device verifies trust metadata
      ▼
[6] Exact Match Resolution
      │ choose profile + device-support packages + full core release
      ▼
[7] Safe Full UniversalOS Installation
      │ stage → verify → inactive/transactional target → first boot health check
      ▼
[8] Confirmed UniversalOS
      │ shared core/UI/services + profile-specific enablement package
      ▼
[9] Ongoing independent updates
      ├─ core updates: every compatible profile receives the same core release
      ├─ support updates: matching profile/family receives hardware package updates
      └─ bootstrap updates: only when signed target-specific boot compatibility changes
```

## What the phone identifies

Discovery must use technical compatibility facts, not personal data.

| Allowed for profile matching | Forbidden from profile matching |
| --- | --- |
| CPU architecture, SoC/board family, revision class | IMEI/MEID |
| bootloader capability and partition topology | Serial number |
| kernel ABI, device tree class, firmware version range | MAC address |
| storage/power/display/input/network capability state | phone number/SIM identity |
| verified-boot and rollback features | cloud account identifiers |

The device maps local facts to a profile such as `uos.profile.<family>.<architecture>.v1`. The profile determines eligibility; a cloud server cannot override it. See [Signed hardware profile catalog](SIGNED_PROFILE_CATALOG.md) for the exact signed local matching rules.

## Package selection rules

The resolver must choose a complete compatible set, not merely one driver:

```text
profile
  + bootstrap version
  + architecture
  + kernel ABI
  + partition/rollback capability
  + required hardware capability state
  + signed repository metadata
  = core release + device-support set + safe install plan
```

A selected set may include a core image, display/input/audio/network adapters, firmware allowed by provenance policy, sensor/radio services, and configuration. All packages are versioned, signed, hash-checked, staged, and rechecked locally before activation.

An exact match failure is safe: the installer reports the unsupported/missing condition and does not partially flash the full OS.

## Update model

The word "every update" has three separate meanings:

| Update type | Audience | Installation safety |
| --- | --- | --- |
| Core release | All profiles compatible with the core architecture/contract | Inactive A/B or transactional system target, health confirmation, rollback |
| Device-support release | Only profiles/families matching its ABI, firmware, and capability requirements | Staged and matched locally; never installed on a mismatched profile |
| Bootstrap release | Only boards that require an early boot/recovery change | Extra recovery/restore validation; never overwrite the only known-good boot path |

This allows one UniversalOS feature/security release to reach every compatible profile while avoiding a driver update designed for one phone damaging another.

## “Every mobile” support policy

The long-term vision is broad mobile support, including older hardware. The engineering promise is not that unknown, locked, or legally unmaintainable phones magically boot one generic image. A phone becomes compatible when the project has a Bootstrap Capsule, a non-personal profile, lawful required firmware/source inputs, a recovery path, and maintained security evidence.

That is how UniversalOS can grow to many devices without lying about support or copying a separate ROM product for each one.

## Relation to the current prototype

The current `core/universal_core` implementation covers only stages **[5]–[6]**: local profile/package compatibility resolution using synthetic profiles. It deliberately does not yet contain:

- USB bootloader discovery;
- real-device bootstrap-capsule selection;
- a bootable Discovery Base;
- real cryptographic repository metadata;
- a downloader, flasher, or update writer.

The versioned Bootstrap Capsule manifest and simulated Universal Installer discovery input are now implemented as a host-side/synthetic prototype. See [Universal Installer and Bootstrap Capsule contracts](BOOTSTRAP_CONTRACTS.md). The signed registry metadata/trust-root reference is documented in [Signed registry metadata and trust root](REGISTRY_TRUST.md), and verified-target/staged-installation modeling is documented in [Verified target binding and safe installation model](SAFE_INSTALLATION.md). All remain host-side/synthetic until persistent recovery gates are complete.
