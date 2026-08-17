# UniversalOS architecture baseline

## Design objective

Keep the minimum device-dependent code small, auditable, locally available, and securely verified. The shared UniversalOS core must be portable and consume hardware profiles/capabilities, never model-specific product branches. Deliver higher-level functionality through signed, compatible, rollback-safe releases.

```text
 ROM / immutable silicon root
          │
          ▼
 Vendor boot chain / unlock policy
          │ verifies
          ▼
 UniversalOS target bootstrap (device-specific, local)
   boot configuration · kernel · device tree · essential modules/firmware
          │ verifies
          ▼
 Recovery + update agent
   local hardware profile · trust store · rollback policy · rescue UI
          │ resolves signed compatible release metadata
          ▼
 Immutable system slot A/B (or equivalent transactional layout)
   core services · UI shell · security services · optional runtimes
          │
          ▼
 Sandboxed apps and user data
```

## Trust boundaries

| Boundary | Required control |
| --- | --- |
| ROM → bootloader | hardware/vendor verified-boot capability and documented unlock/relock policy |
| Bootloader → bootstrap | signed image verification; key provenance and device binding documented |
| Bootstrap → system slot | verified boot / integrity checks; rollback index or an equivalent anti-downgrade policy |
| Update agent → repository | threshold-signed metadata, expiration, version monotonicity, repository root rotation and revocation |
| Resolver → package | exact target, hardware profile, version, ABI, digest, size, and signer validation before download/install |
| System → app | least privilege, sandboxing, explicit permissions, authenticated IPC, data encryption where applicable |
| Diagnostics → cloud | explicit consent, minimization, redaction, retention policy, and local review/export controls |

## Hardware profile

A hardware profile is a signed, versioned description used for compatibility decisions. It is **not** an untrusted free-form identifier supplied by a remote service.

Minimum fields:

- profile identifier and schema version;
- board/SOC revision, bootloader constraints, partition layout, and rollback capability;
- kernel ABI/configuration and module compatibility;
- required firmware inventory with redistribution/provenance status;
- feature capabilities and known constraints;
- compatible bootstrap and system release ranges;
- test status and issue references;
- signer, creation/expiry, and revocation information.

The local bootstrap reads stable identifiers, maps them to an embedded/verified profile, then asks the resolver for *candidates*. The local policy engine makes the final acceptance decision. The core sees the profile capabilities and contracts, not a phone model name.

## Update lifecycle

1. The agent obtains root/timestamp/snapshot/targets-style signed metadata from one or more mirrors.
2. It validates signer thresholds, versions, expiry, trust-root rotation rules, and package digests before use.
3. It matches the local hardware profile, installed versions, storage availability, power state, and policy to a candidate.
4. It downloads to verified staging storage, validates digest/size/signature again, and writes only the inactive slot or transactional target.
5. It sets a one-time boot attempt and persists an update journal.
6. The new system must report post-boot health within a bounded period. Failure returns to the known-good slot.
7. The agent records a privacy-respecting local update result. Optional reporting is separate.

A server compromise, mirror compromise, captive portal, and replayed old metadata must not cause arbitrary installation.

## Package classes

| Class | Location | Examples | Update rules |
| --- | --- | --- | --- |
| Bootstrap | device-local verified partition | boot config, kernel, DTB, essential firmware | rare, device-specific, recovery-tested |
| Device support | signed package/partition | compatible modules, hardware adapters, approved firmware | exact profile/ABI/version match |
| Core system | immutable system slot | init, system services, shell, settings | atomic, rollback-safe |
| Application runtime | system package | app framework, browser/web runtime | sandboxed, independently versioned where safe |
| Apps | user/application store | user-installed software | per-app signing and permissions; no system trust escalation |
| User data | encrypted writable data partition | files, settings, app data | never overwritten by normal system-slot rollback |

## Initial interface contracts

Before UI implementation, document and test these interfaces:

- `hardware-profile`: read-only profile/query service;
- `update-agent`: check, stage, apply, progress, error, rollback, and release-notes API;
- `power-state`: battery/charging/thermal-safe update preconditions;
- `device-health`: bounded post-update attestation of critical services;
- `recovery`: reset, rescue-log export, reflash instructions, and active-slot selection;
- `settings`: permissions, update policy, privacy/diagnostic consent, accessibility preferences.

## Rejected shortcuts

- Downloading and executing a driver based solely on an online hardware scan.
- Using a single server key with no rotation/revocation or expiration metadata.
- Overwriting the only bootable system partition during an update.
- Advertising a device as supported when camera, modem, recovery, or upgrade behavior is unknown.
- Treating UI-generated code as a replacement for a threat model, hardware abstraction, or system test suite.
