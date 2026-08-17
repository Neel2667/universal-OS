# Signed hardware profile catalog

## Purpose

UniversalOS must not select drivers from an untrusted server response or a marketing model name. After Discovery Base boots, it measures non-personal hardware facts locally and uses a signed profile catalog to select **exactly one** compatible hardware profile.

```text
locally measured facts
  + verified role=profiles metadata
  → one exact signed profile
  → package/capability resolver
  → matching device-support set
```

## Components

| Path | Purpose |
| --- | --- |
| `specs/hardware-profile/measured-facts-v1.json` | Non-personal locally measured facts. |
| `specs/hardware-profile/catalog-v1.json` | Signed `profiles` metadata body. |
| `core/universal_core/profiles.py` | Catalog parser, local matching, ambiguity rejection, and verified loading helper. |
| `tests/test_profiles.py` | Signed catalog, mismatch, ambiguity, and privacy tests. |

## Matching rules

A catalog entry matches only if all of these are true:

```text
architecture
board family
SoC family
revision class
partition model
kernel ABI
```

Board and SoC wildcards are forbidden. Revision wildcard is permitted only after exact board/SoC/architecture/partition/kernel-ABI matching. No profile accepts an IMEI, serial number, MAC address, account identifier, or SIM identity.

No match and multiple matches are both safe failures. The resolver does not choose a "nearest" profile and never stages a support package after ambiguous hardware detection.

## Signed metadata role

The trust root now supports a `profiles` role in addition to `root`, `bootstrap`, and `targets`. `verify_and_load_profiles()` verifies signature threshold, expiry, role, and anti-rollback version state before the catalog is usable.

This is still a host-side reference. Discovery Base must later provide real local facts from trusted boot/kernel/device-tree interfaces and persist the accepted profiles metadata version in authenticated state.
