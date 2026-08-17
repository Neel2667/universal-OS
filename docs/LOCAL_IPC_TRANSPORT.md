# Linux local IPC transport reference

## Purpose

UniversalOS services must not be exposed as a network API and must not trust an application-provided capability string. This reference adds a Linux Unix-domain-socket transport for the existing local service protocol.

```text
Unix-domain socket
  → Linux SO_PEERCRED peer UID/GID/PID
  → platform capability policy
  → strict bounded JSON request
  → UniversalOS service gateway
  → strict bounded response
```

## Implementation

| Path | Purpose |
| --- | --- |
| `core/universal_core/unix_ipc.py` | Unix socket server, `SO_PEERCRED` peer extraction, fixed peer-policy mapping, bounded newline frame reader. |
| `tests/test_unix_ipc.py` | Local socket authorization, permissions, denied update scope, and malformed-wire tests. |

The server has no TCP/IP listener, no URL routing, no bearer-token parser, no driver loading, and no phone transport logic. Its socket is created with mode `0660`; a real image must also use service-manager ownership and mandatory-access-control labels.

## Authentication model

The current `PeerCredentialPolicy` is intentionally a test/reference mapping from local Unix UID to `CallerContext`. A production Discovery Base must derive the mapping from its native service manager and MAC policy. It should grant privileged update/health capabilities only to verified system services, not to a user-facing app process.

`SO_PEERCRED` is Linux-specific. Any other base platform must provide an equivalent authenticated local-peer mechanism before implementing this protocol.

## Wire rules

- Unix socket only; never bind a network port.
- One UTF-8 JSON request per newline-delimited frame.
- Maximum request frame is 64 KiB.
- Invalid/oversized messages get bounded error responses.
- Error responses do not include stack traces, filesystem paths, artifacts, or device identifiers.
- Request envelopes cannot carry a bearer token or claim a capability; the peer policy supplies identity.

## Boundary

This is a host-side Linux reference, not the final Discovery Base daemon. The next native phase must select the system base, define service-manager units/MAC rules, and bind health/update authority to verified boot. No physical device is touched by this socket server.
