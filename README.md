# UniversalOS

> A long-lived, secure, device-adaptive mobile operating-system research project.

UniversalOS aims to make supported mobile hardware useful for longer by separating a small, verified hardware bootstrap from an updateable system and signed device-support packages. It is **not** an attempt to download arbitrary drivers before a phone can boot: the essential boot chain and the device-specific kernel/bootstrap must exist locally and be cryptographically verified.

## Project status

**Planning and architecture phase.** No device is supported yet, and this repository does not provide a flashable operating-system image. The first engineering goal is to select one unlockable Android-family reference device and produce a reproducible, recoverable developer boot path.

## Principles

- **Secure by design:** verified boot, signed metadata and packages, rollback protection, and a local recovery path.
- **Long-lived support:** isolate hardware-dependent code from the core user-space system wherever practical.
- **Explicit compatibility:** support is declared, tested, and versioned per device; it is never assumed from a marketing promise.
- **User control:** no required account for basic device operation; transparent update and diagnostic controls.
- **Reproducible engineering:** documented source provenance, build steps, test evidence, and release artifacts.

## Start here

- [End-to-end project plan](docs/PROJECT_PLAN.md)
- [System architecture](docs/ARCHITECTURE.md)
- [Risk register](docs/RISK_REGISTER.md)
- [Decision log](docs/DECISIONS.md)
- [Definition of done](docs/DEFINITION_OF_DONE.md)
- [Initial GitHub backlog](docs/INITIAL_BACKLOG.md)
- [Proposed implementation blueprint](docs/IMPLEMENTATION_BLUEPRINT.md)
- [Reference-device intake checklist](docs/REFERENCE_DEVICE_INTAKE.md)
- [Contribution guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## Scope boundary for version 0.1

UniversalOS will first target **one community-friendly, bootloader-unlockable Android-family device or an emulator**, with a developer-only installation flow. The initial release will validate the boot, recovery, update, and compatibility model. Broad device support, a consumer app ecosystem, cellular certification, and iPhone support are explicitly out of scope until the reference implementation has passed its gates.

## Working on the project

Use the [GitHub issue tracker](https://github.com/Neel2667/universal-OS/issues) for all planned work and the project board for sequencing. Each pull request must link to an issue, include test evidence, and respect the security and compatibility rules in this repository.

## Current branch

Development work is performed on the `arena/01a00b34-universal-os` branch through pull requests into `main`.
