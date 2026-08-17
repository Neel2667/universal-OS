# ADR-007 — Device admission, maintenance, and retirement policy

- **Status:** Accepted for version 0.1
- **Date:** 2026-08-16
- **Related issue:** [#8](https://github.com/Neel2667/universal-OS/issues/8)

## Support tiers

| Tier | Meaning | Public statement allowed |
| --- | --- | --- |
| `profiled` | Signed profile/spec exists, no installation evidence | Research only |
| `lab` | Bootstrap/recovery or feature work is active | Developer lab only |
| `verified` | Install, update, rollback, recovery, provenance, and feature matrix evidence exists | Named developer-preview support |
| `maintained` | Security owner, regression cadence, provenance, and lifecycle policy exist | Supported according to published scope |
| `retired` | Device cannot meet security/maintenance obligation | No current support claim; recovery/retirement notice remains |

## Admission requirements

A device cannot enter `verified` or `maintained` without:

```text
exact model/revision identity class
approved Bootstrap Adapter/Capsule
signed profile and matching evidence
source/firmware provenance records
offline restore/recovery proof
install/update/rollback evidence
feature matrix with no hidden unknown claims
named security maintenance owner
```

## Retirement rules

A device is retired when a critical unpatchable kernel/firmware defect, absent maintainer, lost recovery path, unresolvable license/provenance issue, or repeated regression prevents honest support. Retirement does not erase documentation; it changes the support claim.
