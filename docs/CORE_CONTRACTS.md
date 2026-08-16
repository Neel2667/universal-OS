# Portable core contracts — reference implementation

## Purpose

This repository now contains the first executable UniversalOS foundation: **portable hardware-profile and package-manifest contracts plus a profile-driven compatibility resolver**. It proves that the core can choose packages through declarative data instead of device-name conditionals. It implements only the signed-registry/exact-match portion of the broader [Discovery Base → full-system delivery flow](BOOTSTRAP_DISCOVERY_FLOW.md).

This is a **host-side reference prototype**, not a bootable operating system, kernel, firmware flasher, driver loader, or production updater. It never connects to a phone, downloads a package, writes storage, or changes a bootloader.

## What is implemented

| Path | Responsibility |
| --- | --- |
| `specs/hardware-profile/schema-v1.json` | Machine-readable v1 profile interchange schema. Profiles define board class and capabilities without personal identifiers. |
| `specs/package-manifest/schema-v1.json` | Machine-readable v1 package metadata schema: compatibility, payload digest, install mode, signer/signature fields, and expiry. |
| `core/universal_core/contracts.py` | Dependency-free structural parser/validator for the security-critical v1 fields. |
| `core/universal_core/resolver.py` | Local resolver that checks architecture, profile, bootstrap range, kernel ABI, capabilities, partition model, and required components. |
| `core/universal_core/trust.py` | Explicit test-only trust-verifier boundary. It is not cryptography. |
| `testdata/` | Two synthetic, structurally different profiles and compatible/incompatible package fixtures. No real handset or vendor firmware is represented. |
| `tools/validate_contracts.py` | Read-only local fixture validation and resolution demonstration. |
| `tests/test_contracts.py` | Standard-library unit tests. |

## Deliberate security boundary

`FixtureTrustVerifier` accepts only fixed test markers such as `fixture:fixture-root:trusted`. It exists so that the resolver policy can be tested without an external dependency. It provides **zero cryptographic security** and is forbidden from any artifact-download, signing, or release path.

Before a device-support package or image exists, this component must be replaced by a reviewed implementation of signed repository metadata, threshold trust roles, key rotation/revocation, expiration, and real cryptographic verification as planned in issue #10.

## Run locally

Python 3.11+ and no third-party packages are required:

```sh
python3 tools/validate_contracts.py
python3 -m unittest discover -s tests -v
```

Expected fixture resolution:

```text
uos.profile.synthetic.cedar-armv7-v1: core=uos.core.armv7@0.1.0; support=[display-service, input-service]; rejected=4
uos.profile.synthetic.orion-arm64-v1: core=uos.core.arm64@0.1.0; support=[display-service, input-service]; rejected=4
```

The synthetic ARM64 and ARMv7 profiles prove that the same resolver source selects different core/device-support packages strictly through profile contracts. No Mi A2/Pixel/Samsung model name appears in the core code.

## Resolver acceptance rules

A package is considered only when all of these checks succeed locally:

1. fixture trust verifier accepts the signer, marker, and metadata expiry;
2. package architecture includes the profile architecture;
3. package profile list includes the exact profile or the `*` shared-core marker;
4. bootstrap version satisfies the declared range;
5. device-support kernel ABI matches exactly when declared;
6. each required capability is locally marked `working`;
7. requested install mode is compatible with the profile partition model; and
8. every profile-required device-support component has a compatible candidate.

A missing core or required device component is a hard failure. Incompatible or untrusted packages are retained as non-sensitive rejection reasons for future UI/audit work.

## Next implementation gates

1. Replace fixture trust with signed test-repository metadata and real cryptography.
2. Add profile signature/provenance validation and versioned schema migration rules.
3. Add an update-state journal plus a staging/rollback simulator.
4. Build an architecture-independent system-service interface around this resolver.
5. Only after recovery/trust gates pass, feed a real lab device profile into the process.
