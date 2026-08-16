# Persistent transaction, staging, preflight, and health contracts

## Purpose

The prior installation model was in-memory. This layer adds host-side reference components for the operational safety checks required before UniversalOS can stage a full matched system:

```text
preflight
  → persist verified transaction state
  → stage digest-addressed artifacts
  → request one first boot
  → obtain fresh local health report
  → commit or recover known-good target
```

These modules remain local simulations. They do not access the Mi A2 battery, partitions, boot control, recovery, or USB transport.

## Components

| Path | Purpose |
| --- | --- |
| `core/universal_core/preflight.py` | Evaluates supplied battery, external-power, free-space, partition, and offline-recovery conditions without touching hardware. |
| `core/universal_core/persistence.py` | Atomic current/previous JSON journal snapshots with integrity digests and corruption fallback; digest-addressed local payload staging. |
| `core/universal_core/health.py` | Fresh, local, profile/boot-target-bound post-boot health-report policy. |
| `core/universal_core/install.py` | Extended with safe serialisation/deserialisation for the persistent journal. |

## Preflight policy

A normal full-system transaction is blocked when any of these apply:

- unsafe single-slot partition layout;
- battery below policy threshold without external power;
- insufficient free space for all payloads plus a reserve;
- no offline recovery path;
- invalid hardware measurements.

The result returns every blocking reason rather than choosing a risky best-effort path.

## Crash-safe journal model

`JournalStore` writes JSON snapshots using a temporary file, file `fsync`, atomic replacement, directory `fsync`, and a separately persisted prior valid snapshot. Each snapshot includes an SHA-256 integrity digest over its sequence number and serialised install journal.

This unkeyed digest detects accidental corruption; it is **not** an authorization mechanism against an attacker who can rewrite the journal and digest. A device implementation must bind journal state to verified boot and authenticated/encrypted local storage. On a corrupt current snapshot, the store loads the previous valid snapshot rather than continuing from unverified state. This is a reference pattern; a device implementation must map it to the selected filesystem/partition and power-loss model.

## Staging model

`StagingStore` uses SHA-256 digest-addressed file names. It rechecks bytes before storing and again before returning staged content. It receives already verified artifacts; it is not a downloader and does not decide package compatibility.

## Health model

A health report is accepted only when all required local services are `ready`, the report is fresh, and its profile/boot target match the requested first boot. A stale, failed, unknown, wrong-profile, or wrong-target report cannot commit an update.

Authenticating the health service against measured/verified boot state is still required before hardware work.

## Deliberate boundary

No component in this document writes a phone partition or claims device recovery. The next gate is an architecture-independent service boundary around these policies, followed by a device-specific recovery proof on a disposable laboratory profile.
