# Contributing to UniversalOS

Thank you for helping build UniversalOS. This project is in its architecture phase; well-supported research, test plans, threat-model feedback, and documentation are valuable contributions.

## Before starting

1. Search existing [issues](https://github.com/Neel2667/universal-OS/issues) and read the project plan.
2. Use an issue to discuss any non-trivial change before investing substantial implementation time.
3. Never upload vendor firmware, proprietary binaries, private signing keys, credentials, or personal device data unless the project has a documented legal and secure process that permits it.
4. Record source, binary, firmware, and model inputs according to [the provenance policy](docs/PROVENANCE_POLICY.md) before distribution work.
5. Do not claim a device/feature is supported without the evidence required by `docs/DEFINITION_OF_DONE.md`.

## Workflow

- Create or select an issue and assign the appropriate type, priority, milestone, and risk labels.
- Branch from the current project development branch, make a focused change, and submit a pull request.
- Use `Refs #123` for partial work and `Fixes #123` only for a complete solution.
- Include test evidence and documentation updates in the PR description.
- Keep generated images, build directories, caches, and large binary artifacts out of Git unless explicitly requested and reviewed.

## Review expectations

Reviewers check correctness, update/recovery impact, security, privacy, source provenance, license implications, support-matrix accuracy, accessibility, and maintainability. A UI-only change may still be rejected if its implied system behavior is undefined or unsafe.

## Communication

Use public issues for normal bugs, ideas, and planning. Follow [SECURITY.md](SECURITY.md) for vulnerabilities or sensitive exploit paths.
