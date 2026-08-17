# Initial GitHub backlog

This is a navigation index for the initial, deliberately bounded backlog. **GitHub Issues are the live source of truth** for acceptance criteria, labels, status, and discussion. Work moves through milestones only with the evidence required by [the definition of done](DEFINITION_OF_DONE.md).

## Sequence rules

- Complete the M0 decisions before committing to a device-specific implementation.
- M1 designs are reviewed against the threat model before M2/M3 code is treated as a supported image.
- The recovery path comes before normal over-the-air delivery; atomic update and fault injection come before a preview release.
- Google Stitch design exploration continues in M5, but a generated screen becomes a product component only after it has documented behavior, accessibility states, and stable service contracts.
- `blocked` is used when a named dependency is incomplete. A later milestone cannot bypass a Red risk without an explicit recorded decision.

## M0 — Foundation and decisions

| Issue | Outcome | Primary dependencies |
| --- | --- | --- |
| [#1](https://github.com/Neel2667/universal-OS/issues/1) | Publish project foundation and GitHub workflow | — |
| [#2](https://github.com/Neel2667/universal-OS/issues/2) | Approve v0.1 charter and success criteria | #1 |
| [#3](https://github.com/Neel2667/universal-OS/issues/3) | ADR-001 reference device selection | #2 |
| [#4](https://github.com/Neel2667/universal-OS/issues/4) | ADR-002 base system/hardware foundation | #3 |
| [#5](https://github.com/Neel2667/universal-OS/issues/5) | Source, firmware, and license provenance policy | #1 |
| [#6](https://github.com/Neel2667/universal-OS/issues/6) | Initial threat model | #1 |
| [#7](https://github.com/Neel2667/universal-OS/issues/7) | ADR-005 privacy/diagnostics/account policy | #2, #6 |
| [#8](https://github.com/Neel2667/universal-OS/issues/8) | ADR-007 device admission/maintenance/retirement policy | #2, #3 |

**Current ADR-001 evidence:** [Xiaomi Mi A2 (`jasmine_sprout`) candidate evaluation](DEVICE_EVALUATIONS/xiaomi-mi-a2-jasmine-sprout.md) and [proposed ADR-001](adr/ADR-001-reference-device.md). The device is research-only until every acceptance gate is met.

## M1 — Compatibility and trust design

| Issue | Outcome | Primary dependencies |
| --- | --- | --- |
| [#9](https://github.com/Neel2667/universal-OS/issues/9) | Versioned hardware-profile schema | #3, #4, #6 |
| [#10](https://github.com/Neel2667/universal-OS/issues/10) | ADR-004 signed metadata/key lifecycle | #6 |
| [#11](https://github.com/Neel2667/universal-OS/issues/11) | Compatibility resolver/package-admission policy | #9, #10 |
| [#12](https://github.com/Neel2667/universal-OS/issues/12) | Partition, recovery, anti-rollback model | #3, #4, #6 |
| [#13](https://github.com/Neel2667/universal-OS/issues/13) | Security/update/device validation matrix | #9–#12 |

## M2 — Reproducible developer platform

| Issue | Outcome | Primary dependencies |
| --- | --- | --- |
| [#14](https://github.com/Neel2667/universal-OS/issues/14) | Reproducible build environment | #4, #5 |
| [#15](https://github.com/Neel2667/universal-OS/issues/15) | CI policy and validation gates | #1, #14 |
| [#16](https://github.com/Neel2667/universal-OS/issues/16) | Release provenance, SBOM, retention plan | #5, #10, #14 |
| [#17](https://github.com/Neel2667/universal-OS/issues/17) | Emulated profile/update-state console | #9, #11, #13 |

## M3 — First-device bootstrap and recovery

| Issue | Outcome | Primary dependencies |
| --- | --- | --- |
| [#18](https://github.com/Neel2667/universal-OS/issues/18) | Reference-device bootstrap feasibility spike | #3–#5, #12, #14 |
| [#19](https://github.com/Neel2667/universal-OS/issues/19) | Tested recovery/reflash path | #12, #18 |
| [#20](https://github.com/Neel2667/universal-OS/issues/20) | Feature-by-feature bring-up matrix | #18, #19 |
| [#21](https://github.com/Neel2667/universal-OS/issues/21) | Verified boot/post-boot health contracts | #3, #4, #6, #12, #18 |

## M4 — Secure update path

| Issue | Outcome | Primary dependencies |
| --- | --- | --- |
| [#22](https://github.com/Neel2667/universal-OS/issues/22) | Signed test repository/metadata verifier | #6, #10, #14 |
| [#23](https://github.com/Neel2667/universal-OS/issues/23) | Compatibility resolution and safe staging | #9, #11, #19, #22 |
| [#24](https://github.com/Neel2667/universal-OS/issues/24) | Atomic apply/confirmation/rollback | #12, #19, #21, #23 |
| [#25](https://github.com/Neel2667/universal-OS/issues/25) | OTA fault-injection/recovery suite | #13, #24 |

## M5 — System experience prototype

| Issue | Outcome | Primary dependencies |
| --- | --- | --- |
| [#26](https://github.com/Neel2667/universal-OS/issues/26) | Experience principles and user journeys | #2, #7 |
| [#27](https://github.com/Neel2667/universal-OS/issues/27) | Stitch concepts → accessible design system | #7, #10, #12, #26 |
| [#28](https://github.com/Neel2667/universal-OS/issues/28) | System-shell prototype | #9, #11, #12, #27 |
| [#29](https://github.com/Neel2667/universal-OS/issues/29) | Performance/battery/accessibility budgets | #3, #26, #28 |

## M6 — App strategy and developer preview

| Issue | Outcome | Primary dependencies |
| --- | --- | --- |
| [#30](https://github.com/Neel2667/universal-OS/issues/30) | ADR-003 app compatibility/runtime model | #4, #6 |
| [#31](https://github.com/Neel2667/universal-OS/issues/31) | App sandbox, permissions, package signing | #6, #30 |
| [#32](https://github.com/Neel2667/universal-OS/issues/32) | Developer kit and reference application plan | #14, #16, #30, #31 |
| [#33](https://github.com/Neel2667/universal-OS/issues/33) | Preview release/incident/support operations | #7, #8, #19, #24, #30 |

## Review cadence

1. Triage new issues weekly: remove `needs-triage`, set type/area/priority/risk/milestone, name dependencies, and close duplicates.
2. Review Red risks and all blocked issues before beginning a new milestone.
3. Review the device matrix and source-provenance inventory before publishing any installable artifact.
4. Hold a release-readiness review before every developer preview or key/signing policy change.
