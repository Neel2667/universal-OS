# UniversalOS managed workstreams

This is the central execution view. Workstreams can progress independently where dependencies permit; merge/release gates remain sequential and security-first.

| Stream | Current state | Completed evidence | Next gate |
| --- | --- | --- | --- |
| Product and governance | In progress | charter framework, risks, issues, milestones, contribution/security policy | formal v0.1 charter approval |
| Universal contracts | Prototype complete | profiles, capsules, package/target metadata, resolver schemas/tests | Rust migration test vectors |
| Trust and update safety | Prototype complete | Ed25519 threshold metadata, target binding, rollback/preflight/journal model | real test-key repo + QEMU persistence/rollback |
| Native service boundary | Prototype complete | capability protocol and local Unix peer-authenticated IPC model | native Rust service processes + systemd/MAC policy |
| Build/Discovery Base | Starting | ADR-002 accepted, build strategy declared | pinned toolchain + QEMU ARM64 image |
| Device enablement | Research only | Mi A2 lab evaluation and intake/recovery checklist | QEMU gates, then real recovery proof |
| UX and apps | Deferred | service contracts available | system image/recovery/update proof |
| AI | Excluded from core scope | idea intentionally removed | none unless future product decision reopens it |

## Coordination rules

1. No physical-device work bypasses recovery, trust, provenance, or QEMU rollback gates.
2. A workstream may use parallel research/prototyping, but only a reviewed, tested result enters the shared core.
3. Every implementation must retain profile-driven behavior; no device-name conditionals in the UniversalOS core.
4. The QEMU Discovery Base is the next critical-path deliverable.
