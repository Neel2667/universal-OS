# UniversalOS universality model

## Decision in plain language

UniversalOS is being designed as **one portable operating-system core**, not as a separate OS product for every phone. A Xiaomi Mi A2, Pixel, or future device may be used as a test laboratory, but it must never define a fork of the UniversalOS product.

The project goal is a universal architecture that can be adapted to many old and new devices through small, independently versioned device-enablement packages. The visible system, security model, update client, user services, application model, and design system remain the same across supported devices.

## What "universal" can truthfully mean

| Universal promise | Meaning |
| --- | --- |
| One product core | One source tree and shared system behavior for all supported device profiles. |
| Portable system releases | Core system releases do not contain one model's private drivers or UI fork; they target an architecture and stable compatibility contracts. |
| Hardware adaptation | A versioned device profile selects the correct local bootstrap and signed device-support packages. |
| Continuous support model | Updating the core system does not require rebuilding every hardware component, when the device compatibility contract remains valid. |
| Transparent support | Every device is listed with an exact support tier, tested features, security status, and recovery evidence. |

It does **not** mean that one identical binary can begin executing on every phone ever made. Before an OS can access cloud networking or discover hardware, each phone's immutable ROM/bootloader requires a locally available, SoC/board-compatible boot image, device tree, storage path, and often proprietary firmware. Some devices have permanently locked bootloaders or unavailable source/firmware. A project must not pretend those constraints do not exist.

The objective is therefore: **universal core, minimal device-specific enablement, no per-device product forks.**

## Four-layer architecture

```text
1. Device trust and bootstrap layer              small, local, signed, target-compatible
   ROM / bootloader → boot configuration → kernel + device tree + essential firmware

2. UniversalOS device-enablement layer          standardized contracts, per profile packages
   hardware discovery → verified profile → capability registry → safe module/firmware adapter

3. UniversalOS core                              shared across profiles of the same architecture
   init · security · package/update agent · settings · shell services · app/runtime APIs

4. User and application layer                    portable, sandboxed, profile-aware only through APIs
   system UI · applications · accessibility · user data
```

Only layer 1 must necessarily start with device-specific knowledge. Layers 2–4 are the UniversalOS product.

## The product installation journey

The desired user flow is: **Discovery Base boots → hardware is identified locally → exact signed support set is selected → full UniversalOS is staged safely → ongoing profile-aware updates continue.**

The one technical prerequisite is that a small target-compatible Bootstrap Capsule must be present before Discovery Base can begin. It is a compatibility adapter, not a separate per-device OS. See [Bootstrap, discovery, and full-system delivery flow](BOOTSTRAP_DISCOVERY_FLOW.md) for the complete state sequence and update model.

## Boot and adaptation sequence

```text
A. Local verified bootstrap starts on known board/SoC
B. Bootstrap reads stable local hardware facts
C. Local policy maps facts to an embedded or signed hardware profile
D. UniversalOS core starts with a safe minimal capability set
E. Network becomes available only after required local drivers are working
F. Update agent obtains signed metadata from one or more mirrors
G. Compatibility resolver selects optional device-support packages that exactly match
H. System activates compatible modules/services and reports real capabilities
```

The cloud distributes candidate packages. It does **not** decide whether a package is trusted and cannot provide the first driver needed to read storage, show a display, establish a secure connection, or boot safely.

## UniversalOS package families

| Family | Shared or profile-specific | Purpose |
| --- | --- | --- |
| `uos-core` | Shared per CPU architecture | Immutable base system, services, shell APIs, security controls, updater. |
| `uos-profile` | Profile-specific, small | Signed declarative hardware identity, capabilities, partition/rollback constraints, ABI requirements. |
| `uos-bootstrap` | Board/SoC-specific | Locally bootable kernel/device tree/early modules/recovery integration. |
| `uos-device-support` | Profile/family-specific | Approved kernel modules, firmware adapters, hardware service implementations, calibrated settings. |
| `uos-app-runtime` | Shared, versioned | Sandboxed application compatibility/runtime components. |
| `uos-app` | Portable | Third-party or system application packages. |

A new device port should normally add a profile, bootstrap, and narrowly scoped device-support package—not duplicate `uos-core`, the shell, or normal applications.

## Device portability contract

Every bootstrap/profile pair must expose a stable contract to the core:

- architecture and kernel ABI;
- verified boot and rollback capabilities;
- active/inactive or transactional partition model;
- immutable device identity class with no personal identifiers;
- storage, display, input, power, network, audio, sensor, and radio capability states;
- required firmware/module versions and provenance status;
- recovery entry and safe log-export capabilities;
- feature state: working, partial, unavailable, untested, blocked, or unsafe.

The core must consume these contracts rather than hard-code checks such as "if device is Mi A2". A profile is a data/control boundary, not an excuse for model-specific behavior to leak into the product.

## Cloud driver-delivery rules

1. **No cloud-first boot:** essential early drivers and required firmware are present in the local verified bootstrap.
2. **No arbitrary executable delivery:** every optional module/firmware package has a digest, signature, profile/ABI range, version, provenance record, expiry, and rollback policy.
3. **Local decision enforcement:** a package is accepted by the local compatibility resolver only after metadata and exact profile checks pass.
4. **Atomic changes:** device-support updates use staging, inactive/transactional targets, health confirmation, and rollback where device layout permits.
5. **Offline resilience:** a working phone remains usable when mirrors/cloud services are unavailable; recovery never depends on the ordinary network path.
6. **Legal and safety gate:** proprietary firmware is not copied or redistributed until its source/license path is reviewed; radio/emergency features remain unclaimed until tested.

## Support tiers

| Tier | Definition | Public promise |
| --- | --- | --- |
| `profiled` | Identity/profile exists; no install claim | Research only. |
| `lab` | Bootstrap, recovery, and core contract are being tested by maintainers | Developer hardware only; known limitations. |
| `verified` | Install, update, rollback, recovery, and required feature matrix have passing evidence | Named developer-preview support. |
| `maintained` | A security owner, update cadence, provenance inventory, and regression testing are active | Supported according to the published lifecycle. |
| `retired` | The device cannot meet maintenance/security obligations | No new support claim; recovery/documentation policy remains published. |

The number of devices is never a quality metric. A universal OS earns trust by adding profiles without weakening evidence or security criteria.

## Development strategy

1. Implement the architecture-independent contracts and their simulated fixtures first.
2. Use the Mi A2 only as an early **lab profile** to prove that contracts meet a real phone's boot/recovery constraints.
3. Build a Device Enablement Kit: profile schema, bootstrap packaging rules, compatibility tests, source/provenance inventory, and recovery checklist.
4. Add a second structurally different device only after the first profile works. This proves that the core is portable rather than a Mi A2-specific design.
5. Add device families through the same admission gates, continuously improving reuse of common SoC/kernel/firmware components.

## Anti-patterns we will reject

- A universal UI over a different hand-maintained OS fork for each model.
- A server telling an unverified phone to execute a driver based on a hardware scan.
- Treating an unlocked bootloader as proof that a device is supportable.
- Including unique identifiers such as IMEI, serial number, account identifiers, or MAC addresses in a profile.
- Promising every device—including permanently locked or unmaintainable hardware—before recovery and security evidence exists.
