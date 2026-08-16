# UniversalOS native service protocol contract

## Purpose

The shared UniversalOS core needs a stable local IPC boundary. A future UI, recovery shell, health daemon, and device-enablement adapter must use defined services instead of bypassing update/recovery policy.

This repository now contains a **transport-independent reference protocol** and a host-side dispatcher. It is not an internet API and must not be exposed on a network port.

```text
native local transport with peer identity
  → caller capability context
  → strict request envelope
  → shared profile/update/health/recovery service policy
  → strict response envelope
```

## Protocol files

| Path | Purpose |
| --- | --- |
| `specs/service-protocol/request-v1.json` | Local IPC request envelope. |
| `specs/service-protocol/response-v1.json` | Success/failure response envelope. |
| `specs/service-protocol/capabilities-v1.json` | Capability vocabulary. |
| `core/universal_core/protocol.py` | Strict host-side parser, authorizer, and dispatcher. |

## Capability model

| Capability | Allowed operation |
| --- | --- |
| `uos.device.read` | Read non-personal profile/capability/update status. |
| `uos.update.read` | Read update target/state. |
| `uos.update.request-first-boot` | Request the bounded first boot after staging. |
| `uos.health.report` | Submit the privileged local health report that can commit or roll back. |
| `uos.recovery.read` | Read a redacted recovery report. |

A regular application/UI must not receive `uos.health.report` or direct hardware-update privileges. It can display status and request user-approved actions through a separately authorized system component.

## Native implementation requirements

The reference `CallerContext` is injected by tests. It is **not authentication** by itself. A native device implementation must derive caller identity and capabilities from authenticated local mechanisms such as:

- Unix-domain socket peer credentials;
- OS service manager identity;
- mandatory access-control label/policy;
- verified-boot state for privileged health/update services; and
- explicit user authorization for recovery-log export.

No request payload may contain a bearer token, private key, device serial, IMEI, account identifier, or raw driver blob.

## Implemented behavior

`LocalServiceGateway` supports profile status, update status, first-boot request, privileged health report, and redacted recovery report. It returns bounded error codes and does not leak traceback, payload, filesystem, or staging-path data across the service boundary.

## Boundary

A host-side Linux Unix-socket transport using `SO_PEERCRED` is now provided in [Linux local IPC transport reference](LOCAL_IPC_TRANSPORT.md). Service supervision, Linux MAC policy, verified-boot measurements, and a real system UI remain required. Nothing here connects to or changes a physical phone.
