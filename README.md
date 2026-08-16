# UniversalOS

> A long-lived, secure, device-adaptive mobile operating-system research project.

UniversalOS aims to make supported mobile hardware useful for longer through **one portable OS core** with small, signed device-enablement packages. It is **not** an attempt to download arbitrary drivers before a phone can boot: the essential boot chain and a minimal target-compatible bootstrap must exist locally and be cryptographically verified. The system UI, services, update client, app model, and security policy are shared—not forked per phone.

## Project status

**Planning and architecture phase.** No device is supported yet, and this repository does not provide a flashable operating-system image. The first engineering goal is to prove the portable core and device-enablement contracts with a reproducible, recoverable developer boot path on a lab device; that laboratory device does not define a separate product build.

## Principles

- **Secure by design:** verified boot, signed metadata and packages, rollback protection, and a local recovery path.
- **Long-lived support:** isolate hardware-dependent code from the core user-space system wherever practical.
- **Explicit compatibility:** support is declared, tested, and versioned per device; it is never assumed from a marketing promise.
- **User control:** no required account for basic device operation; transparent update and diagnostic controls.
- **Reproducible engineering:** documented source provenance, build steps, test evidence, and release artifacts.

## Start here

- [End-to-end project plan](docs/PROJECT_PLAN.md)
- [System architecture](docs/ARCHITECTURE.md)
- [Universality model](docs/UNIVERSALITY_MODEL.md)
- [Bootstrap-to-full-system flow](docs/BOOTSTRAP_DISCOVERY_FLOW.md)
- [Universal Installer and Bootstrap Capsule contracts](docs/BOOTSTRAP_CONTRACTS.md)
- [Portable core contracts](docs/CORE_CONTRACTS.md)
- [Signed registry metadata and trust root](docs/REGISTRY_TRUST.md)
- [Verified target binding and safe installation model](docs/SAFE_INSTALLATION.md)
- [Persistent transaction, staging, preflight, and health contracts](docs/PERSISTENCE_AND_PREFLIGHT.md)
- [Universal system-service boundary](docs/SYSTEM_SERVICE_BOUNDARY.md)
- [Native local service protocol](docs/NATIVE_SERVICE_PROTOCOL.md)
- [Linux local IPC transport reference](docs/LOCAL_IPC_TRANSPORT.md)
- [Local Intelligence architecture](docs/LOCAL_AI_ARCHITECTURE.md)
- [Risk register](docs/RISK_REGISTER.md)
- [Decision log](docs/DECISIONS.md)
- [Definition of done](docs/DEFINITION_OF_DONE.md)
- [Initial GitHub backlog](docs/INITIAL_BACKLOG.md)
- [Proposed implementation blueprint](docs/IMPLEMENTATION_BLUEPRINT.md)
- [Reference-device intake checklist](docs/REFERENCE_DEVICE_INTAKE.md)
- [Mi A2 candidate evaluation](docs/DEVICE_EVALUATIONS/xiaomi-mi-a2-jasmine-sprout.md)
- [Contribution guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## Scope boundary for version 0.1

UniversalOS will first validate **one portable core** against an emulator and a community-friendly, bootloader-unlockable Android-family lab device, with a developer-only installation flow. The initial release validates the reusable boot, recovery, update, profile, and compatibility contracts—not a device-specific product fork. Broad device support, a consumer app ecosystem, cellular certification, and iPhone support are explicitly out of scope until the reference implementation has passed its gates.

## Portable core prototype

The device-independent foundation is available in `core/universal_core`. It first selects a minimal Bootstrap Capsule from a synthetic non-personal discovery record, then resolves portable hardware profiles and package manifests without any phone model logic. It is a **host-side prototype only** and cannot flash or boot a phone.

```sh
python3 -m pip install -e .
python3 tools/validate_contracts.py
python3 -m unittest discover -s tests -v
```

See [Portable core contracts](docs/CORE_CONTRACTS.md) for its security boundary and next gates.

## Working on the project

Use the [GitHub issue tracker](https://github.com/Neel2667/universal-OS/issues) for all planned work and the project board for sequencing. Each pull request must link to an issue, include test evidence, and respect the security and compatibility rules in this repository.

## Current branch

Development work is performed on the `arena/01a00b34-universal-os` branch through pull requests into `main`.
