# Release readiness, health attestation, audit, and device evidence

This batch adds the remaining host-side gates needed before a release can be honestly described.

## Device enablement validation

`tools/validate_device_enablement.py` validates a port manifest. Verified/maintained tiers require tested offline recovery; maintained tiers cannot hide `untested`, `blocked`, or `unsafe` feature states.

## Release manifest and SBOM

`tools/generate_sbom.py` creates SPDX-lite provenance output. `tools/generate_release_manifest.py` binds a release ID, source revision, target/profile, SBOM digest, test count, and provenance state. `test-only` does not imply a releasable image.

## Health attestation

`core/universal_core/attestation.py` models a signed health report bound to profile, boot target, update ID, issue/expiry times, and required ready services. A future native service must bind its attestation key to verified boot; this host model only proves the cryptographic contract.

## Audit chain

`core/universal_core/audit.py` provides an append-only hash-chain model for non-personal update/recovery events. It detects corruption/order changes but is not attacker-resistant without authenticated device storage.

## Device test matrix

`specs/device-enablement/test-matrix-v1.json` standardizes evidence for boot, recovery, update, rollback, and feature status. A device is never "supported" merely because it booted once.
