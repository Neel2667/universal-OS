# Verified target binding and safe full-system installation model

## Purpose

This reference layer connects the signed-registry plan to the intended UniversalOS installation path:

```text
verified targets metadata
  → exact manifest bytes
  → exact payload bytes
  → compatibility resolution
  → staged inactive/transactional target
  → first-boot health confirmation
  → commit or rollback
```

It remains a pure host-side model. It cannot download, write, flash, reboot, select a physical slot, or modify a device.

## Verified target binding

`specs/repository-metadata/targets-v1.json` defines signed `targets` metadata. Every target binds:

- a target ID and package ID;
- the exact SHA-256 digest and byte size of its package manifest; and
- the exact SHA-256 digest and byte size of its payload.

`core/universal_core/artifacts.py` receives bytes already obtained by a future downloader and fails closed unless all checks match the verified descriptor. It then parses the package manifest and requires the manifest's own declared payload digest/size to agree with signed targets metadata.

Only a `VerifiedTargetArtifact` should feed `resolve_verified_manifests`. This is the transition away from the earlier fixture-only package trust path.

## Installation journal model

`core/universal_core/install.py` models an append-only transaction state machine:

```text
idle
  → metadata-verified
  → artifacts-verified
  → staged
  → pending-first-boot
  → committed

staged / pending-first-boot
  → rolled-back
```

| Partition model | Normal full-system behavior |
| --- | --- |
| A/B | Stage the inactive target, first-boot it once, commit only after health confirmation. |
| Transactional | Stage the next immutable transaction generation, then commit after health confirmation. |
| Single-slot | Reject normal full-system install. A separately designed recovery-only flow is required; in-place overwrite is not accepted. |

Power interruption or failed health confirmation retains the earlier known-good target in the model.

## What is now covered by tests

- signed targets metadata binds the exact manifest and payload bytes;
- payload and manifest tampering are rejected before compatibility resolution;
- a descriptor cannot silently bind a manifest with a different package ID;
- verified targets feed the profile-based resolver;
- A/B commit happens only after healthy first boot;
- failed health and interruption roll back to the known-good A/B target;
- transactional generation selection is deterministic;
- unsafe single-slot normal installation is rejected.

## Deliberate limits before hardware work

The next implementation must add a reviewed downloader/staging store, persistent crash-safe journal storage, available-space and power preflight, real boot-control integration, device-health attestation, and actual recovery proof. This model does not authorize flashing the Mi A2 or any other phone.
