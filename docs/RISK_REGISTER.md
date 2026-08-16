# Risk register

Risk ratings are reassessed at every milestone. **Red** risks block a release or architecture decision until an owner records an accepted mitigation.

| ID | Risk | Likelihood | Impact | Rating | Mitigation / decision | Trigger | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-01 | Bootloader is locked or unlock wipes/irreversibly restricts a target | High | Critical | Red | Select only documented unlockable targets; publish restore path before port begins | candidate cannot be safely restored | Unassigned |
| R-02 | Essential drivers/firmware are proprietary or cannot be redistributed | High | Critical | Red | maintain provenance inventory; use user-extraction process only where lawful; reject unsupported targets | source/license audit fails | Unassigned |
| R-03 | Cloud package compromise leads to malicious installation | Medium | Critical | Red | offline root of trust; threshold signing; expiry; digest validation; key rotation/revocation; independent review | invalid signing or security test failure | Unassigned |
| R-04 | Interrupted update bricks a device | Medium | Critical | Red | A/B or transactional updates; journal; health-check rollback; USB recovery; fault injection | recovery test fails | Unassigned |
| R-05 | Hardware diversity makes "all devices" impossible to sustain | High | High | Red | narrow support matrix; reusable profiles; device certification gates; honest limitations | device added without evidence | Unassigned |
| R-06 | Radio, emergency calling, DRM, payments, or biometrics do not function/certify | High | High | Red | keep out of initial promise; feature-specific validation and compliance review | feature advertised without validation | Unassigned |
| R-07 | Kernel/vendor code has unpatched security defects | Medium | Critical | Red | target lifecycle policy; CVE triage; upstream preference; security support window per target | unpatchable critical CVE | Unassigned |
| R-08 | Build output cannot be reproduced or attributed | Medium | High | Amber | pinned tools; build records; SBOM/provenance; independent rebuilds | artifact source differs | Unassigned |
| R-09 | Key theft or accidental signing-key exposure | Medium | Critical | Red | separate test/prod keys; hardware-backed/offline production policy; access review; incident playbook | key suspected exposed | Unassigned |
| R-10 | Privacy-invasive telemetry or cloud dependency damages trust | Medium | High | Amber | account-free core operation; opt-in diagnostics; data map; retention/deletion policy | network needed for basic boot/use | Unassigned |
| R-11 | UI feels attractive but is slow/inaccessible | Medium | Medium | Amber | performance and accessibility budgets; prototype test; reduced-motion and screen-reader review | budget regression | Unassigned |
| R-12 | Android app compatibility creates excessive privilege/attack surface | High | High | Red | decide app model explicitly; sandbox design; staged compatibility scope | runtime bypasses platform isolation | Unassigned |
| R-13 | Maintainer capacity cannot keep devices updated | High | High | Red | support tiers; removal/sunset policy; automation; contributor onboarding | no security owner for target | Unassigned |
| R-14 | Open-source license obligations are missed | Medium | High | Amber | SPDX/source manifest; notices; legal review; reproduce source offers | undocumented source/blob | Unassigned |
| R-15 | Regional regulations and radio/safety requirements are not considered | Medium | High | Amber | limit developer preview; compliance checklist before consumer claims | public distribution scope expands | Unassigned |
| R-16 | A remote service outage prevents recovery/update or normal use | Medium | High | Amber | cached metadata, multiple mirrors, offline rescue image; no cloud-required boot | single endpoint dependency | Unassigned |
| R-17 | Public roadmap creates unsupported expectations | High | Medium | Amber | publish scope and support definitions; avoid dates until evidence exists | marketing claim exceeds matrix | Unassigned |

## Risk-handling rules

1. A Red risk cannot be marked "accepted" by an implementation contributor alone; it needs a recorded maintainer decision.
2. Every device-support pull request updates relevant risk evidence and the device test matrix.
3. Security incidents use the private process in `SECURITY.md`; do not expose exploit details in public issues before a fix is available.
4. A mitigation is not complete without a verification method and recorded result.
