# Reference-device evaluation — Xiaomi Mi A2 (`jasmine_sprout`)

- **Status:** candidate under evaluation; **not supported** and no flashing is authorized by this document.
- **Decision issue:** [#3 — ADR-001](https://github.com/Neel2667/universal-OS/issues/3)
- **Evaluation date:** 2026-08-16
- **User-provided identity:** Xiaomi Mi A2. Exact model/region, RAM/storage configuration, installed build, bootloader state, and physical condition are still unknown.

> Do not confuse this phone with the newer **Redmi A2**. This evaluation is for the 2018 Android One **Xiaomi Mi A2**, conventionally called `jasmine_sprout` by the Android ROM ecosystem.

## Provisional conclusion

The Mi A2 is a **credible research and developer bring-up candidate**, because it has a documented Android custom-ROM history, an unlock path described in the LineageOS guide, public Xiaomi kernel-source history, a known Android device codename, and modest 4/6 GB RAM hardware that makes it useful for testing a lightweight system.

It is **not currently a credible public-preview or long-term supported-device candidate**. Its vendor support ended years ago, its reported kernel base is 4.4, current LineageOS support is explicitly discontinued, and essential vendor firmware/blobs will need a legal/security provenance review. The project may use it to validate the bootstrap, recovery, profile, and atomic-update architecture—but must not promise current security support, telephony, cameras, biometrics, or daily-driver reliability.

## Known technical profile

| Field | Evidence / current understanding | Confidence |
| --- | --- | --- |
| Android ROM codename | `jasmine_sprout` | High |
| Release generation | July 2018 | High |
| SoC / architecture | Qualcomm SDM660 (Snapdragon 660), arm64, Adreno 512 | High |
| RAM/storage family | 4 GB or 6 GB RAM; 32/64/128 GB storage variants | High |
| Display | 5.99-inch, 1080 × 2160 | High |
| Device kernel line | Linux 4.4 reported by the LineageOS device page | High |
| Last public official ROM observed | `V11.0.28.0.QDIMIXM`, Android 10-era release, published by Xiaomi Community in 2021 | Medium–High |
| Boot/update partition topology | Must be measured from the actual handset; do not infer from ROM guides alone | Unknown |
| Exact variant / regional modem | Must be confirmed from the actual handset without collecting IMEI/serial data | Unknown |

## Positive evidence

1. **Existing development knowledge.** The LineageOS device page identifies the Mi A2 as `jasmine_sprout`, documents its SDM660/arm64 hardware, and provides historic install/build guidance. The build guide includes device-specific source preparation and vendor-blob extraction guidance. This lowers basic discovery cost, but is not a support commitment from LineageOS.
2. **Documented unlock feasibility.** The LineageOS installation guide describes enabling OEM unlocking and using a standard fastboot unlock command. It also clearly says unlocking erases user data. This is evidence to investigate the unlock path—not permission to unlock before data backup and recovery verification.
3. **Public kernel-source history.** Xiaomi's public `MiCode/Xiaomi_Kernel_OpenSource` repository exposes a `jasmine-q-oss` branch. On 2026-08-16, the branch resolved to `71b2d56625574d530ee61f05b7e25f7c302e9796`. The branch must be cloned, licensed, built, and compared against the selected device build before it can be treated as an input.
4. **Relevant low-to-mid-range constraints.** The 4/6 GB RAM and SDM660 class is useful for establishing an honest baseline for boot time, memory pressure, image size, power use, and UI responsiveness on an older phone.
5. **Historically documented restore artifacts.** Xiaomi Community posts provide Android 10-era fastboot ROM links for `jasmine`, including the 2021 `V11.0.28.0.QDIMIXM` release. Artifact availability and checksums must still be independently verified before any recovery claim is made.

## Blocking risks and required mitigations

| Gate | Why it blocks a supported image | Required evidence before moving on |
| --- | --- | --- |
| Exact handset identity | "Mi A2" alone does not establish regional variant, installed firmware, capacity, or board revision | model/variant, RAM/storage, Android build, generic product/board properties; never IMEI/serial |
| OEM unlock status | An unavailable/greyed-out OEM unlock control or unknown policy blocks development installation | user confirms status in Developer options; later, a non-destructive fastboot connectivity check |
| Data and restore | Unlocking wipes data; an experimental image without a verified restore path is unsafe | encrypted/local data backup completed and independently verified; exact stock restore artifact/digest/procedure reviewed |
| Vendor blobs / firmware | Radio, camera, GPU, DSP, Wi-Fi/Bluetooth and other functions may require proprietary pieces | component inventory, source/extraction method, redistributability decision, hash and target-build compatibility |
| Kernel security | Kernel 4.4 and a 2021-era vendor stack cannot satisfy a current public security-support promise by default | CVE/patch-gap assessment; feasible maintenance plan; explicit support window or rejection |
| Community maintenance | The current Lineage device page says the Mi A2 is no longer maintained | a named UniversalOS maintainer and a sustainable upstream/security plan, or limited research-only scope |
| Partition and rollback model | An unsafe assumption about slot/recovery/rollback behavior can brick the phone | read-only partition/slot inventory on the actual device and a state diagram reviewed against it |
| Cellular/safety functionality | Regional carrier behavior, IMS/VoLTE, emergency calling, and certifications cannot be assumed | feature-specific physical tests and compliance decision; otherwise mark unclaimed/disabled |

## Support classification

| Classification | Mi A2 status now | Meaning |
| --- | --- | --- |
| Architecture research target | **Candidate** | May be used to validate schemas, emulator contracts, build tooling, and eventually developer-only bootstrap/recovery work after gates pass. |
| Developer bring-up target | **Conditional** | Requires exact-device intake, backup, verified restore, provenance review, and explicit owner approval. |
| Public developer-preview target | **Rejected for now** | Cannot be approved until kernel/vendor-security and recovery evidence meet the project definition of done. |
| Consumer/daily-driver target | **Out of scope** | No telephony, emergency, camera, biometric, DRM/payment, or security-lifecycle promise is justified. |

## Safe intake steps — no unlocking or flashing

1. Record the information requested in the [reference-device intake checklist](../REFERENCE_DEVICE_INTAKE.md): exact model, region, RAM/storage, Android build number, whether OEM unlocking is visible, device condition, and whether later data wipe is acceptable.
2. Back up personal data now, but **do not enable OEM unlocking or run unlock/flash/relock commands yet**.
3. Confirm normal stock behavior before experimentation: boot, display/touch, charging, Wi-Fi, Bluetooth, audio, cameras, fingerprint, GPS, calls/SMS, and data—without publishing sensitive logs or identifiers.
4. Identify a trustworthy factory-restore route and verify the exact artifact filename, hash/signature, tooling, and whether the procedure needs an unlocked or critical-unlocked bootloader.
5. Only then schedule a separately reviewed, developer-only unlock/recovery rehearsal on a device whose data may be erased.

## Evidence sources

- [LineageOS device page: Xiaomi Mi A2 (`jasmine_sprout`)](https://wiki.lineageos.org/devices/jasmine_sprout/) — current device status, specifications, kernel line, boot-mode references.
- [LineageOS installation guide](https://wiki.lineageos.org/devices/jasmine_sprout/install/) — historic unlock/recovery procedure and data-wipe warning.
- [LineageOS build guide](https://wiki.lineageos.org/devices/jasmine_sprout/build/) — historic source/build and proprietary-blob extraction context.
- [Xiaomi kernel source repository](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/tree/jasmine-q-oss) — `jasmine-q-oss` public source branch; branch head recorded above.
- [Xiaomi Community: Mi A2 `V11.0.28.0.QDIMIXM` fastboot/recovery release](https://c.mi.com/thread-3781218-1-0.html) — historical stock-ROM source link; not independently validated as a recovery artifact yet.

Sources establish feasibility/history, not legal redistribution rights, present-day vulnerability status, or an endorsement of a specific flashing tool.
