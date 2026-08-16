# UniversalOS system-service boundary

## Purpose

The universal system needs one stable API between shared services/UI and all future hardware-enablement packages. This repository now provides a host-side reference coordinator that composes the existing contracts without hard-coding a phone model.

```text
verified artifacts
  → profile resolver
  → preflight policy
  → persistent transaction journal
  → digest-addressed staging
  → first-boot request
  → health decision
  → commit / rollback / redacted recovery report
```

## Implemented boundary

`core/universal_core/services.py` provides `UniversalSystemServices`.

| API | Shared-system responsibility |
| --- | --- |
| `status()` | Exposes non-personal profile, capability, active-target, and update state for a future settings/UI service. |
| `stage_verified_update()` | Resolves only verified target artifacts, evaluates preflight, stages payloads, and persists a staged transaction. |
| `request_first_boot()` | Moves a staged transaction to one bounded first-boot attempt. |
| `confirm_first_boot()` | Uses a fresh local health report to commit or roll back. |
| `recover()` | Rolls an uncommitted transaction back to the known-good modeled target. |
| `recovery_report()` | Exports redacted state/event data without payload bytes, filesystem paths, identifiers, or account data. |

The service is deliberately unaware of a phone name. Device packages provide a profile and verified artifacts; the shared core makes the same policy decisions for every compatible profile.

## Safety conditions

- `stage_verified_update()` accepts only `VerifiedTargetArtifact` inputs from the verified targets pipeline.
- The resolved core and every required device-support component must have a verified artifact.
- Preflight must pass before a journal/staging transaction starts.
- A future UI cannot directly force a commit; commit requires a matching fresh health report.
- Recovery reports expose status code/event information only, not staging paths or payload contents.

## Explicit limits

This is not an IPC daemon, boot service, device driver, USB installer, or physical recovery implementation. It is the portable policy boundary that those later platform components must implement. It does not communicate with the Mi A2 or any other device.

The next phase is to specify native on-device service protocols and then create a disposable, recovery-proven lab adapter. No physical installation is authorized merely because this host-side API exists.
