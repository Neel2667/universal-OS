# Implementation blueprint — proposed reference architecture

> **Status: proposed.** This document creates an implementation map for the planning phase. It deliberately does not select the first device, kernel base, programming language, package format implementation, or app runtime; those are the decisions tracked in [ADR-001 through ADR-004](DECISIONS.md).

## 1. First buildable slice

The first buildable slice is intentionally narrow. It is not a phone replacement and it does not claim support for radios, cameras, biometrics, payments, or Android applications.

```text
reference device / emulator
  └─ target bootstrap starts
      └─ recovery-capable core starts
          └─ trusted profile is read locally
              └─ update agent verifies repository metadata
                  └─ compatibility resolver selects or rejects a test payload
                      └─ state console reports each decision and recovery state
```

**Demonstration result:** a known target can identify itself, reject an invalid/mismatched/replayed test package, stage an approved test package safely, and preserve/recover its earlier bootable state. This is the architecture proof for the long-lived, lightweight direction selected for version 0.1 planning.

## 2. Proposed repository layout

The layout becomes active only after ADR-002; do not create empty implementation folders merely to look complete.

```text
universal-OS/
├── docs/                       # product, ADRs, architecture, evidence templates
├── specs/                      # versioned, machine-readable interface schemas
│   ├── hardware-profile/
│   ├── repository-metadata/
│   ├── package-manifest/
│   └── update-state/
├── bootstrap/                  # target-specific boot integration; no proprietary blobs in Git
│   └── <device-codename>/
├── core/                       # profile reader, resolver, updater, recovery contracts
│   ├── profile/
│   ├── resolver/
│   ├── updater/
│   ├── recovery/
│   └── health/
├── services/                   # documented IPC/service implementations
│   ├── hardware-profile/
│   ├── update-agent/
│   └── device-health/
├── ui/                         # Stitch-derived design tokens, shell, accessibility fixtures
│   ├── design-system/
│   └── system-shell/
├── tools/                      # reproducible-build, signing-test, fixture, and validation tools
├── testdata/                   # non-secret fixtures; deliberately invalid package metadata allowed
│   ├── profiles/
│   ├── repository/
│   └── update-scenarios/
├── tests/                      # unit, contract, integration, emulator, and hardware test definitions
│   ├── contract/
│   ├── integration/
│   └── hardware/
└── third_party/                # only manifests/patches/notices; never unexplained vendor binaries
```

Generated images, download caches, firmware blobs, production signing material, user logs, and extracted device partitions are excluded by `.gitignore` and must be handled through the provenance policy.

## 3. Component map and responsibility boundaries

| Component | Responsibility | Must not do |
| --- | --- | --- |
| Target bootstrap | Start on the named hardware; expose trusted identifiers; verify the next stage; provide minimal recovery entry | Download unverified code or claim generic support |
| Profile reader | Map locally measured identifiers to a signed hardware profile | Treat a remote reply as the source of local hardware truth |
| Trust client | Validate signed repository metadata, root rotation, expiry, threshold roles, and revocations | Select/execute an update based on network availability alone |
| Compatibility resolver | Select a candidate only if all local constraints match; explain rejection | Load package code to learn whether it is compatible |
| Stager/installer | Validate again, write inactive/transactional target, journal state | Modify the only bootable system image in place |
| Device-health service | Report a bounded, local, authenticated post-boot success result | Require a cloud connection or make success dependent on a UI animation |
| Recovery | Choose known-good boot path; offer safe log export/restore | Depend on the ordinary system slot or network service |
| System shell | Display state and invoke documented service actions | Bypass update, permission, or recovery policy |
| Build/release tooling | Produce traceable test artifacts, metadata, SBOM/provenance | Store production keys in repository/CI |

## 4. Versioned contracts

All contracts are schema-versioned. A newer client may read an older valid schema only through an explicit compatibility rule; an unknown mandatory field or schema must fail safely.

### 4.1 Hardware profile — conceptual `v1`

```json
{
  "schema_version": 1,
  "profile_id": "org.universalos.reference.example.v1",
  "match": {
    "board": ["example-board"],
    "soc": ["example-soc-revision-a"],
    "bootloader_constraints": {"unlockable": true, "rollback_protection": "known"}
  },
  "boot": {
    "partition_model": "ab",
    "kernel_abi": "example-abi-1",
    "minimum_bootstrap_version": "0.1.0"
  },
  "firmware_requirements": [
    {
      "component": "essential-startup-firmware",
      "version_range": ">=1.0.0 <2.0.0",
      "provenance_ref": "inventory-placeholder",
      "redistribution": "pending-review"
    }
  ],
  "capabilities": {
    "display": "required",
    "touch": "required",
    "storage": "required",
    "wifi": "unknown",
    "cellular": "not-claimed"
  },
  "signing": {"profile_key_id": "test-profile-key", "expires": "2030-01-01T00:00:00Z"}
}
```

This is an illustrative fixture only. The real schema must avoid personal identifiers such as IMEI, serial number, account identifiers, or Wi-Fi/Bluetooth addresses. A profile records compatibility classes, not a person or an individual handset.

### 4.2 Package manifest — conceptual `v1`

```json
{
  "schema_version": 1,
  "package_id": "org.universalos.system.reference",
  "version": "0.1.0-test.1",
  "kind": "core-system",
  "targets": ["org.universalos.reference.example.v1"],
  "requires": {
    "bootstrap": ">=0.1.0 <0.2.0",
    "kernel_abi": "example-abi-1",
    "minimum_free_bytes": 4294967296,
    "power": {"minimum_battery_percent": 50, "allow_external_power": true}
  },
  "payload": {
    "digest": {"algorithm": "sha256", "value": "fixture-not-a-real-digest"},
    "bytes": 0,
    "install_mode": "inactive-slot"
  },
  "rollback": {"index": 1, "data_migration": "none"},
  "release_notes_ref": "signed-metadata-reference"
}
```

The manifest is accepted only after the repository metadata and manifest signature/digest have already been validated. It never grants itself a new permission or substitutes for a verified profile.

### 4.3 Update state model

```text
IDLE
  → CHECKING_METADATA
  → REJECTED_METADATA | RESOLVING
RESOLVING
  → NO_COMPATIBLE_RELEASE | PREFLIGHT
PREFLIGHT
  → DEFERRED_POWER | DEFERRED_STORAGE | DEFERRED_NETWORK | STAGING
STAGING
  → REJECTED_PAYLOAD | READY_TO_APPLY
READY_TO_APPLY
  → APPLYING_INACTIVE_TARGET
APPLYING_INACTIVE_TARGET
  → PENDING_FIRST_BOOT
PENDING_FIRST_BOOT
  → CONFIRMED_HEALTHY | BOOT_FAILED_OR_UNCONFIRMED
BOOT_FAILED_OR_UNCONFIRMED
  → ROLLED_BACK | RECOVERY_REQUIRED
```

Every terminal state must contain a stable reason code and a user-safe message. Logs can include technical detail only after redaction rules are applied.

## 5. Update security sequence

1. Bootstrap starts from the target's documented local trust chain.
2. The profile reader obtains stable local identifiers and selects an embedded/verified profile.
3. The trust client validates root, timestamp, snapshot, and target metadata (or the selected equivalent) using threshold signatures, version monotonicity, expiry, revocation, and root-rotation rules.
4. The resolver intersects profile, package target, bootstrap/version range, ABI, firmware requirements, storage, power, and local rollback policy.
5. The stager downloads to a verified temporary location and checks length/digest/signature again.
6. The installer writes only the inactive A/B slot or accepted transactional equivalent, preserving an update journal.
7. The boot manager tries the new target once. The health service confirms critical local services within a bounded window.
8. Confirmation commits the new state. Missing/failed confirmation triggers known-good fallback or explicit offline recovery.

The following are always rejection paths, never "best effort": unknown hardware profile, expired metadata, unsigned or below-threshold metadata, replayed targets, incompatible ABI, revoked signer, package digest mismatch, unsupported partition model, insufficient safe staging space, and an untrusted rollback request.

## 6. Initial test fixtures and gates

Before real-device flashing, the `testdata/` set must include:

| Fixture | Expected result |
| --- | --- |
| Valid supported profile + current signed package | candidate resolves; safe staging is permitted |
| Unknown board/revision | no package selected; clear unsupported-device reason |
| Valid profile + wrong kernel ABI | package rejected before staging |
| Expired/replayed metadata | metadata rejected; no writable target touched |
| Valid metadata + tampered payload | digest failure; no inactive slot marked bootable |
| Revoked signing key | package/metadata rejected even if otherwise compatible |
| Insufficient space/low power | deferred state; no partial install |
| Interrupted write/first boot | journaled fallback to known-good state |

A real device test adds exact model/revision, bootloader state, input components, build and artifact digest, external power status, and recovery outcome. Do not record IMEI, serial, account data, or unredacted logcat dumps in public fixtures/issues.

## 7. Stitch-to-shell workflow

Google Stitch remains a parallel design input, not a privileged system-code generator.

1. Capture the journey and state being explored (e.g., update deferred for low battery).
2. Generate and compare visual concepts in Stitch.
3. Select a concept against the product principles and include the design source/version in the design record.
4. Extract design tokens and explicit component states: normal, focused, loading, empty, offline, error, blocked, recovery, large text, reduced motion, and high contrast.
5. Map visible actions only to documented contracts in section 3.
6. Implement the component with accessibility labels and budget measurement.
7. Test it using mock service responses before allowing it to drive a device operation.

A beautiful concept that has no recovery/error/offline state is incomplete and cannot be accepted into the system shell.

## 8. First implementation order

| Order | Deliverable | Issue gate |
| --- | --- | --- |
| 1 | Product charter, target device, base-system, provenance, threat-model decisions | #2–#6 |
| 2 | Schemas and recovery/update specifications with invalid fixtures | #9–#13 |
| 3 | Pinned build environment and automated contract checks | #14–#17 |
| 4 | Target bootstrap plus independently tested recovery | #18–#21 |
| 5 | Test repository, resolver, atomic apply, fault injection | #22–#25 |
| 6 | Stitch-derived system shell and measured experience | #26–#29 |
| 7 | Application model, sandbox, developer kit, preview operations | #30–#33 |

## 9. Decisions intentionally postponed

- Exact language/framework for core services and UI.
- Exact target device and partition implementation.
- Hosting provider, mirror topology, and production signing hardware.
- Android application compatibility level, if any.
- Telephony, proprietary firmware extraction, payments/DRM/biometrics, and consumer distribution.

Those decisions need evidence from the first target and must not be hidden in a code scaffold.
