# Signed Bootstrap Capsule catalog

## Purpose

The first device-specific compatibility artifact is the Bootstrap Capsule, so it must be authorized by the same local trust model as profiles and packages. A computer, mirror, or USB transfer cannot select a capsule merely by naming one.

```text
local preliminary discovery record
  + verified role=bootstrap metadata
  → exact compatible Bootstrap Capsule
  → Discovery Base boot
```

## Components

| Path | Purpose |
| --- | --- |
| `specs/bootstrap-capsule/catalog-v1.json` | Signed `bootstrap` role metadata body. |
| `core/universal_core/bootstrap.py` | Verified catalog loader and selection path. |
| `tests/test_signed_bootstrap_catalog.py` | Ed25519 catalog verification, matching, newest selection, mismatch, and ambiguity tests. |

## Rules

- Role `bootstrap` metadata must pass root role threshold, expiry, and anti-rollback checks before the catalog is loaded.
- Capsule selection then requires exact architecture, board family, SoC family, partition model, and transport compatibility.
- An unlocked bootloader remains a local requirement.
- Board/SoC wildcards remain forbidden.
- No compatible capsule or more than one newest capsule is a safe failure.
- Inner capsule fields do not supersede the signed catalog authority; the signed metadata role authorizes the candidate catalog.

## Relation to USB installer

The USB Universal Installer may fetch and transfer signed bootstrap catalog metadata, but the device verifies that metadata locally. USB transport is not a trust root. Once a capsule boots Discovery Base, the common UniversalOS transfer protocol takes over for profiles, manifests, and payloads.
