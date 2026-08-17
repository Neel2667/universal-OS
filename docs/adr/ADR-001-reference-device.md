# ADR-001 — Select the reference device

- **Status:** Proposed — candidate evaluation in progress
- **Date:** 2026-08-16
- **Related issue:** [#3](https://github.com/Neel2667/universal-OS/issues/3)
- **Candidate:** Xiaomi Mi A2 (`jasmine_sprout`)

## Context

UniversalOS needs one physical device that can safely validate its core claim: a small local bootstrap identifies an approved hardware profile, verifies compatible signed updates, preserves a known-good system, and recovers safely. The project owner has a Xiaomi Mi A2 available.

A reference device is not chosen merely because it is available. It needs a documented unlock policy, a reproducible restore path, enough source/provenance information for a lawful developer image, and a sustainable security/support boundary.

## Options considered

| Option | Benefits | Costs / risks |
| --- | --- | --- |
| Use the Mi A2 as a research-only initial target | Physical access; documented custom-ROM history; public kernel branch; relevant older hardware constraints | Vendor support ended; reported 4.4 kernel; LineageOS no longer maintains it; proprietary firmware; unknown exact variant/condition |
| Use emulator/host contracts only before selecting hardware | No bricking/data-loss risk; fast contract iteration | Cannot validate boot, recovery, firmware, partition, or real performance behavior |
| Select a newer unlockable device | Better prospective security/support and likely modern partition features | Requires acquiring hardware and restarting target research |

## Proposed decision

Treat the Xiaomi Mi A2 as a **research candidate**, not a supported UniversalOS device, while the project completes the gates in `docs/DEVICE_EVALUATIONS/xiaomi-mi-a2-jasmine-sprout.md`.

If the exact handset is unlockable and a restore rehearsal, source/provenance review, partition model, and security assessment succeed, it may become the **developer-only bring-up target** for phases M2–M4. It will remain ineligible for public developer-preview support unless the project demonstrates a defensible kernel/vendor-security maintenance plan and meets the device-support definition of done.

## Consequences

- First design and emulator work can proceed using a `jasmine_sprout` profile fixture marked `research-only`.
- No image, driver package, firmware, bootloader-unlock instruction, or public support claim will be published yet.
- The project will not use the device's IMEI, serial number, account information, or unique radio identifiers in profiles, logs, test fixtures, or Git.
- A newer device remains a likely future public-preview candidate even if the Mi A2 succeeds as the architecture laboratory.

## Acceptance evidence required to accept or reject this ADR

- [ ] Exact model/region/RAM/storage/installed-build intake completed without sensitive identifiers.
- [ ] OEM unlocking state and non-destructive fastboot connectivity verified on this handset.
- [ ] A trusted stock-restore route and artifact verification procedure reviewed, then independently rehearsed when data wipe is approved.
- [ ] `jasmine-q-oss` kernel branch and required device/vendor inputs have a source/license/provenance inventory.
- [ ] Actual partition/slot/rollback constraints measured and mapped to the recovery design.
- [ ] CVE/patch-gap and maintainership assessment concludes whether the target is research-only, developer-only, or rejected.
- [ ] Named maintainer accepts the resulting support tier and limitations.
