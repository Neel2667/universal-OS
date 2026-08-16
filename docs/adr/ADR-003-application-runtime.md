# ADR-003 — Initial application compatibility and runtime model

- **Status:** Accepted for v0.1 developer planning
- **Date:** 2026-08-16
- **Related issue:** [#30](https://github.com/Neel2667/universal-OS/issues/30)

## Decision

UniversalOS v0.1 uses two application classes:

```text
native-system
  → Rust/C-backed trusted system services only
  → signed and built as part of UniversalOS image

wasi-component
  → future third-party portable app format
  → sandboxed capability-based runtime
  → explicit user grants only
```

Android compatibility, APK runtime, browser-first applications, and arbitrary native third-party binaries are out of scope for v0.1. They may be proposed later only after the sandbox, runtime, and update/recovery paths have physical proof.
