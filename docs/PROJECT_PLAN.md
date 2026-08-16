# UniversalOS — end-to-end project plan

## 1. Mission and first proof

**Mission:** deliver one portable mobile operating-system core that extends the useful life of supported hardware through small, signed device-enablement packages—without weakening boot security, hiding device limitations, or creating a product fork per phone.

**Version 0.1 proof:** on one selected unlockable target (or a faithful emulator before hardware), an experienced developer can:

1. verify prerequisites and unlock status;
2. install a signed bootstrap image through a documented recovery path;
3. boot a minimal UniversalOS environment;
4. identify the exact hardware profile locally;
5. fetch only a signed, compatible system/device-support release;
6. apply it atomically to an inactive slot;
7. reboot successfully; and
8. recover automatically or manually from a deliberately bad update.

This proof is more important than a polished launcher. It establishes the product's hardest promise: safe, durable support while demonstrating that the core is independent of a specific handset.

## 2. Non-negotiable technical reality

A mobile device cannot start from a generic network-only image. Before reliable networking, storage, display, touch, and radio access are available, the device needs a chain of locally available, device-compatible firmware and software. Some of that code is proprietary and some devices have permanently locked bootloaders.

Therefore, UniversalOS uses a **portable-core and device-enablement model**:

- **Device trust/bootstrap layer:** local, minimal, signed, and specific to an approved board/SoC family. It includes the boot configuration, kernel/device tree, essential modules, firmware required to start, and recovery integration.
- **Device-enablement layer:** a small, versioned hardware profile plus compatible module/firmware/service packages behind stable contracts.
- **UniversalOS core:** a signed, updateable, hardware-independent user-space system, shell, services, app/runtime APIs, and approved optional packages. It must not be forked per phone.

The cloud is a signed distribution service—not a root of trust and not a source of executable code that bypasses local verification.

## 3. Product choices that must be decided before implementation

| Decision | Decision criteria | Gate |
| --- | --- | --- |
| First device | unlockable bootloader, documented restore process, kernel source availability, active community, affordable availability, usable mainline/vendor support | ADR-001 |
| Base technology | ability to reuse legal hardware enablement, update isolation, security posture, Android-app strategy, team skill | ADR-002 |
| App model | Android compatibility, web-first, Linux applications, or a new SDK; security and developer adoption implications | ADR-003 |
| Update metadata | signed roles, threshold keys, expiry, rollback policy, mirror strategy | ADR-004 |
| Data/privacy model | account optionality, telemetry default, crash-report consent, diagnostic retention | ADR-005 |
| UI direction | Stitch-generated concept becomes an implementable design system only after accessibility and performance review | ADR-006 |

No device image should be built until ADR-001 and ADR-002 are accepted.

## 4. Delivery phases and exit gates

### Phase 0 — Governance and discovery

**Outputs**
- public product charter, glossary, decision log, issue taxonomy, contribution and security processes;
- device-candidate comparison and legal/source-provenance assessment;
- threat model and a measurable version-0.1 success definition.

**Exit gate:** a maintainer approves one initial target and architecture direction. Open blocking risks have owners and deadlines.

### Phase 1 — Compatibility and trust design

**Outputs**
- versioned hardware profile schema;
- signed repository metadata specification, key roles, expiry, rotation, revocation, and mirror model;
- package compatibility resolver specification;
- partition/slot, recovery, rollback, and factory-reset design;
- test matrix for supported and intentionally unsupported hardware.

**Exit gate:** design review proves that a mismatched, unsigned, expired, revoked, or rollbacked package cannot be installed by the normal updater.

### Phase 2 — Reproducible developer platform

**Outputs**
- hermetic/reproducible build instructions and pinned build environment;
- emulator path where practical, static analysis, SBOM/provenance plan, and artifact signing in a non-production test environment;
- a minimal shell/console that can report device identity and update state.

**Exit gate:** two clean environments generate equivalent, traceable test artifacts and automated tests run on every pull request.

### Phase 3 — First-device bootstrap and recovery

**Outputs**
- target-specific bootstrap image based on legally redistributable components;
- boot state measurement and verified boot integration;
- user-visible rescue mode, USB restore instructions, and boot-failure diagnostics;
- hardware bring-up checklist: display, touch, storage, charging, audio, Wi-Fi, Bluetooth, camera, sensors, and cellular are each explicitly tested or marked unsupported.

**Exit gate:** the reference device survives ten consecutive update/reboot cycles and recovers from power loss at defined interruption points. No claimed hardware feature lacks test evidence.

### Phase 4 — Secure updates and compatibility delivery

**Outputs**
- signed test repository; compatibility resolver; staged rollout controls; offline/limited-network behavior; A/B (or equivalent) atomic installation; post-boot health confirmation;
- update history, release notes, rollback UX, and an emergency revocation path.

**Exit gate:** fault-injection tests prove safe behavior for lost power, unavailable server, compromised mirror, invalid metadata, full storage, and incompatible package attempts.

### Phase 5 — System experience prototype

**Outputs**
- Stitch-assisted visual concepts translated into an accessible design system;
- launch surface, navigation, settings, notification model, multitasking concept, onboarding, update screen, and recovery UX;
- performance budgets for boot time, RAM, frame pacing, background work, battery impact, and APK/image size.

**Exit gate:** usability review completes on representative small/large screens; core interactions work without cloud access; accessibility baseline is met.

### Phase 6 — Application and service strategy

**Outputs**
- selected app/runtime model; application permissions; sandboxing; package signing; developer documentation; sample application;
- data backup/export/migration design and a policy for proprietary services.

**Exit gate:** an untrusted app cannot read protected data or gain system privileges in the documented threat model. A third-party developer can build and install a sample app from clean instructions.

### Phase 7 — Developer preview

**Outputs**
- named, signed preview release; known-issues list; rollback image; support channel; telemetry/bug-report consent flow; release criteria;
- device matrix with exact versions and limitations.

**Exit gate:** a small invited group independently completes installation and recovery; critical defects and security findings have documented resolution or release-blocker decisions.

### Phase 8 — Expansion, beta, and sustainable operations

**Outputs**
- device-porting kit; CI hardware test strategy; key management ceremony; release cadence; incident response; contributor/reviewer onboarding; compatibility certification process.

**Exit gate:** each added device meets the same recovery, update, source-provenance, and support evidence as the reference device. Do not add devices simply to enlarge a list.

## 5. Work sequence

1. Close foundation documentation and decide ownership.
2. Select the first device and technology base with evidence.
3. Write and review trust/update/compatibility specifications.
4. Establish reproducible builds before generating a flashable image.
5. Implement and test recovery before normal OTA updates.
6. Implement signed, atomic updates before designing advanced UI.
7. Bring up one device feature-by-feature with published support status.
8. Build the UI prototype in parallel only against stable service contracts.
9. Add an app model after the base security boundary is tested.
10. Release only with independent install, rollback, and recovery validation.

## 6. GitHub operating model

- **Issues are the source of work.** Every issue has a type, priority, owner, acceptance criteria, risk/security note where relevant, and dependencies.
- **Milestones represent exit gates**, not calendar promises. An issue moves only when its acceptance evidence is attached.
- **Pull requests link an issue** using `Fixes #<number>` only when all acceptance criteria are complete. Partial work uses `Refs #<number>`.
- **No direct production secrets** are stored in GitHub Actions, the repository, screenshots, logs, or issues. Test keys are marked non-production.
- **Security vulnerabilities are reported privately** under `SECURITY.md`, not as public issues.
- **Issues are closed with evidence:** test command/output, device revision, artifact digest, screenshots/logs with sensitive data removed, and rollback result if applicable.

## 7. Metrics and quality bars

| Area | Initial measure |
| --- | --- |
| Support honesty | Every advertised device/version has a published test matrix and known limitations. |
| Update safety | 100% of release candidates pass normal, interrupted, invalid, and rollback update scenarios. |
| Reproducibility | Independent clean build produces matching or explainably equivalent signed inputs/artifacts. |
| Security | No unsigned package path; severity-critical vulnerabilities block releases until triaged/remediated. |
| Performance | Budgets set per target before implementation; regressions require an issue and approval. |
| Accessibility | Keyboard/switch navigation where relevant, scalable text, contrast, screen-reader labels, reduced-motion behavior. |
| Privacy | Basic operation works without account; collection is opt-in and documented. |

## 8. Explicit non-goals for the first release

- Supporting every Android device, every legacy phone, or locked iPhones.
- Running cloud-delivered drivers prior to local verified boot.
- Promising cellular, cameras, biometrics, DRM, payments, or emergency calling until certified/tested on a named target.
- Replacing a mature app ecosystem overnight.
- Shipping a consumer-facing image before recovery and update failure handling work.
