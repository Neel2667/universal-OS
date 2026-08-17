# Reference-device evaluation — Xiaomi Mi A2 (`jasmine_sprout`)

- **Status:** candidate under evaluation; **not supported** and no flashing is authorized by this document.
- **Decision issue:** [#3 — ADR-001](https://github.com/Neel2667/universal-OS/issues/3)
- **Evaluation date:** 2026-08-16
- **User-provided identity:** Xiaomi Mi A2, 6 GB RAM, India variant, bootloader already unlocked, currently running Ubuntu Touch. The user reports Android 9 as the provisioning base. Exact model number, storage capacity, Ubuntu Touch channel/build, slot state, boot/vendor image versions, and physical condition are still unknown.

> Do not confuse this phone with the newer **Redmi A2**. This evaluation is for the 2018 Android One **Xiaomi Mi A2**, conventionally called `jasmine_sprout` by the Android ROM ecosystem.

## Actual developer device record — user supplied

| Field | Reported value | Interpretation / verification status |
| --- | --- | --- |
| Bootloader | Unlocked | Removes the first installation barrier; keep it unlocked during research. Do not relock until a correct stock restore image and partition model are verified. |
| Current runtime | Ubuntu Touch | Useful evidence that this handset can boot a Linux-oriented mobile stack. Exact Ubuntu Touch channel/build is needed. |
| Android version | Android 9 | Likely means the Android 9/Halium vendor base that the Mi A2 Ubuntu Touch port requires, rather than the current visible OS. Confirm through read-only baseline data. |
| Memory | 6 GB RAM | Good configuration for a lightweight-system performance baseline; storage capacity still needed. |
| Market | India | Record for modem/firmware and restore-artifact compatibility; this does not by itself identify a unique handset. |

The Ubuntu Touch device page currently describes the Mi A2 port as Halium 9-based, built on the outdated Xenial release, unmaintained, and inactive since 2023. It also warns that the Mi A2 has a buggy fastboot implementation and that the port required a specific Android 9 build before installation. That history confirms the device is a useful lab target, but also makes **baseline preservation and cautious recovery work mandatory**.

## Role in the universal architecture

The Mi A2 is a **non-exclusive lab profile**, not the base OS target and not a model-specific UniversalOS product. It will be used to test whether the portable core, profile schema, device-enablement packages, update process, and recovery contracts work on real hardware. A second structurally different device must later validate that the core did not accidentally become Mi A2-specific.

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

## Safe next steps — preserve Ubuntu Touch; no flashing

The bootloader is already unlocked, so there is no reason to run an unlock command. **Do not run the UBports Installer, re-flash Android 9, change slots, install TWRP, use Mi Flash, or relock the bootloader.** The historical Ubuntu Touch installer can write `vendor` and `boot` and format system/cache/user data; it is not a harmless inspection tool.

1. Make an ordinary user-data backup from Ubuntu Touch first. Verify that copied files open on another device. This is a data backup only, not yet a partition backup.
2. Record the Ubuntu Touch version/channel from Settings → About, the exact marketed model, storage capacity, and a short feature status (display/touch, charging, Wi-Fi, Bluetooth, audio, cameras, GPS, calls/SMS, mobile data, fingerprint).
3. Optionally run the committed [read-only baseline collector](../../tools/device-intake/collect-mi-a2-ubuntu-touch-baseline.sh) from your own computer. It requires an explicit `--consent-read-only` argument, only uses ADB read commands, and never uploads output. Inspect/redact its text before sharing it.
4. Preserve the baseline record and identify a trustworthy stock-restore route. Verify exact artifact filename, hash/signature, region match, tooling, and data-loss/relock consequences before any recovery rehearsal.
5. After the above evidence is reviewed, schedule a separate developer-only **recovery rehearsal**. It must prove return to the current known-good state before UniversalOS writes any bootable partition.

Do not send IMEI/serial numbers, MAC addresses, SIM/phone numbers, account data, unlock tokens, or unredacted full logs.

## Evidence sources

- [Ubuntu Touch device page: Xiaomi Mi A2 (`jasmine_sprout`)](https://devices.ubuntu-touch.io/device/jasmine-sprout/release/xenial/) — current port status, Android 9 prerequisite, fastboot caution, and historic release information.
- [LineageOS device page: Xiaomi Mi A2 (`jasmine_sprout`)](https://wiki.lineageos.org/devices/jasmine_sprout/) — current device status, specifications, kernel line, boot-mode references.
- [LineageOS installation guide](https://wiki.lineageos.org/devices/jasmine_sprout/install/) — historic unlock/recovery procedure and data-wipe warning.
- [LineageOS build guide](https://wiki.lineageos.org/devices/jasmine_sprout/build/) — historic source/build and proprietary-blob extraction context.
- [Xiaomi kernel source repository](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/tree/jasmine-q-oss) — `jasmine-q-oss` public source branch; branch head recorded above.
- [Xiaomi Community: Mi A2 `V11.0.28.0.QDIMIXM` fastboot/recovery release](https://c.mi.com/thread-3781218-1-0.html) — historical stock-ROM source link; not independently validated as a recovery artifact yet.

Sources establish feasibility/history, not legal redistribution rights, present-day vulnerability status, or an endorsement of a specific flashing tool.
