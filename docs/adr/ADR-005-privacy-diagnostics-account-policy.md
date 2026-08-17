# ADR-005 — Privacy, diagnostics, and account policy

- **Status:** Accepted for version 0.1
- **Date:** 2026-08-16
- **Related issue:** [#7](https://github.com/Neel2667/universal-OS/issues/7)

## Decision

UniversalOS basic operation requires **no cloud account**. Boot, recovery, settings, local apps, offline bundles, USB installation, and local diagnostics remain available without sign-in.

Network use is separated into explicit purposes:

| Purpose | Default | Data boundary |
| --- | --- | --- |
| Signed metadata/artifact retrieval | user-initiated or user-configured update policy | mirror sees ordinary network connection metadata; device trust is local signatures |
| Diagnostics | off by default | redacted, reviewable local report; user chooses export destination |
| Crash report | off by default | no automatic upload in v0.1 |
| Account/sync | absent from v0.1 | no account service included |

## Privacy controls

- No IMEI, serial, MAC address, SIM identity, or account identity in profile catalogs, transfer journals, support matrices, or public logs.
- Recovery reports are redacted and user-exported only.
- Saved Wi-Fi details are optional, locally protected, removable, and not required for USB/offline installation.
- A mirror is transport, not identity authority; it cannot select a profile or install code.
- No advertising, behavioral profiling, attention telemetry, or mandatory cloud analytics.

## Consequences

The project must create useful local diagnostics and support flows rather than relying on backend analytics. Future account/sync proposals require a new ADR with data map, encryption, retention/deletion, and export controls.
