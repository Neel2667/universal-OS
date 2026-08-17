# Universal Installer end-to-end rehearsal

## Purpose

The UniversalOS security components now have a single host-side integration rehearsal. It chains the complete decision path without connecting to a phone:

```text
signed bootstrap catalog
  → exact Bootstrap Capsule selection
  → signed profiles catalog
  → locally measured profile selection
  → signed targets catalog
  → USB/offline resumable manifest and payload transfer
  → verified target artifact set
```

## Component

`core/universal_core/installer.py` contains `UniversalInstallerRehearsal`.

It refuses out-of-order behavior. Targets cannot be accepted before the bootstrap and locally matched profile steps complete. Transfer artifacts cannot be accepted unless their target descriptor is already in verified targets metadata.

## What the rehearsal proves

- the installer cannot jump directly from a server response to a package;
- bootstrap, profile, and target roles have separate signature/anti-rollback state;
- preliminary bootloader facts and local Discovery Base facts have distinct purposes;
- USB/offline transport is interchangeable with later network transport because all transfer bytes use the same target binding; and
- exact core and device-support artifacts become available only after every previous gate succeeds.

## Boundary

The rehearsal is not a physical installer. It does not invoke fastboot/ADB, expose a USB gadget, start a network service, write a partition, or boot QEMU. It gives the future Rust Universal Installer a deterministic expected behavior/test vector.
