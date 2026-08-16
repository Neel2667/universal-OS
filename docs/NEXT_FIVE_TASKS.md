# Next five secure delivery tasks

This batch completes five independent, non-native tasks while the Rust/Yocto/QEMU host remains unavailable:

1. **Mirror retrieval model** — HTTPS-only production policy, test-only file mirror fallback, bounded retrieval, no trust granted by transport.
2. **Offline bundle path** — explicit no-phone-internet bundle verification guidance.
3. **Fault matrix** — deterministic interruption and failed-health rollback scenarios.
4. **SPDX-lite SBOM generator** — release provenance output from validated component records.
5. **Device Enablement Kit** — manifest and admission rules preventing per-device core forks.

All remain host-side reference tooling. Native Discovery Base and hardware work remain blocked by the documented build-host prerequisites.
