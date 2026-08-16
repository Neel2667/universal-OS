# UniversalOS connectivity bootstrap and installation data flow

## Objective

A first UniversalOS installation must not require the phone to already have working Wi-Fi, cellular service, an account, a browser, or a large collection of drivers. It must also avoid a long, fragile setup sequence.

The preferred first-install experience is:

```text
Connect phone to a computer with USB
  → Universal Installer detects approved preliminary hardware facts
  → installer downloads signed candidates using the computer's internet
  → installer transfers them through a local USB recovery/data channel
  → phone independently verifies all signed metadata and payload hashes
  → phone boots UniversalOS Discovery Base
```

The phone does **not** need to obtain internet before it has a compatible network driver.

## Why a phone cannot start from a network-only generic image

Before any online hardware detection can occur, the phone needs local compatible code for at least:

```text
boot ROM / bootloader handoff
kernel and device tree
storage
USB recovery or transport
basic memory/timer support
trusted root metadata
```

Display/touch and Wi-Fi are included when the selected installation path requires them. A network driver cannot be safely downloaded before the phone has enough local support to reach the network and verify the result.

This is why UniversalOS uses a small **Bootstrap Capsule**. It is the unavoidable local compatibility adapter, not a separate device-specific UniversalOS product.

## Installation channels

| Channel | First-install support | User experience | Required local device support | Security rule |
| --- | --- | --- | --- | --- |
| **USB Universal Installer** | Required / preferred | Connect cable, approve device, follow one guided flow | bootloader/recovery USB transport, storage | phone verifies every transferred artifact itself; computer is not trusted root |
| **Offline USB package** | Required | Download package on another computer, copy/transfer, install offline | storage + recovery transport | same signed metadata/hash verification; no network needed |
| **Pre-provisioned Wi-Fi** | Optional after Discovery Base boot | user enters/scans Wi-Fi once or imports explicit temporary setup data | selected Wi-Fi driver/firmware in local capsule | credentials are user-approved, encrypted locally, removable |
| **USB tether / host relay** | Optional | phone uses a connected computer's network after boot | USB networking or recovery transfer support | network is transport only; signed metadata remains authority |
| **Ethernet adapter** | Developer/recovery option | attach supported USB-C Ethernet adapter | USB host/network support | same signed repository validation |
| **Cellular / SIM / eSIM** | Later device-specific feature | normal mobile data after verified device support | modem firmware, radio service, APN support, regulation testing | never assumed during initial installation |
| **Bluetooth tethering** | Future convenience option | pair with explicit user action | Bluetooth firmware/service | no use before verified network/device support |

## First-install sequence

```text
0. User downloads Universal Installer on a computer
1. User connects an unlockable supported device through USB
2. Installer reads only allowed preliminary facts through the local boot/recovery protocol
3. Installer shows the candidate profile, capsule version, download size, and recovery warning
4. Installer downloads signed Bootstrap Capsule / Discovery Base candidates using the computer connection
5. Installer transfers bytes over USB; transfer is resumable and does not imply trust
6. Device verifies root → bootstrap/profile/target metadata → manifest → payload digests locally
7. Device starts Discovery Base and re-measures local hardware facts
8. Device chooses exactly one signed hardware profile or stops safely
9. Device receives/transfers the matching full UniversalOS core and device-support set
10. Device stages the system to its inactive/transactional target
11. First boot health check commits or rolls back
```

A computer may improve speed and convenience, but it cannot cause code to run merely by transferring it. The device's embedded trust root and local verifier remain the authority. The resumable transport model is specified in [USB and offline resumable transfer protocol](USB_TRANSFER_PROTOCOL.md).

## Discovery Base networking

Once the Discovery Base is running, it can choose the fastest safe connection route:

```text
if verified USB installer link exists:
    use host-provided signed artifact transfer
else if local Wi-Fi bootstrap capability exists and user supplies a network:
    connect to Wi-Fi and fetch from mirrors
else if offline package is available:
    verify it locally and continue offline
else:
    show a clear recovery/setup screen; do not guess or install partial data
```

A Wi-Fi-capable Bootstrap Capsule contains only the necessary profile-compatible Wi-Fi driver, firmware, and minimal network stack for that route. It does not download an arbitrary first driver from the cloud.

## Data retrieval and verification

```text
mirror / Universal Installer / offline bundle
  → signed root metadata
  → signed Bootstrap / profiles / targets metadata
  → exact package manifest
  → exact payload bytes
  → local SHA-256 check
  → local compatibility resolver
  → staging store
```

Transport may use HTTPS, USB transfer, local offline media, or a future peer relay. Transport security is helpful, but the system does not rely solely on TLS or server identity. A malicious mirror or computer transfer fails because signatures, roles, versions, expiry, profile match, manifest digest, and payload digest must all validate locally.

## Fast onboarding principles

1. **One cable first.** USB installer is the default; Wi-Fi setup is not a prerequisite.
2. **No required account.** Never block boot, recovery, or installation on sign-in.
3. **Few user decisions.** User confirms device, data-wipe/recovery warning, and final installation; technical matching is automatic and inspectable.
4. **Resumable transfers.** Interrupted downloads/transfers resume after digest verification rather than restarting a full image.
5. **Cache safely.** Installer can cache signed artifacts, but the device revalidates every use.
6. **Offline path always exists.** A user can transfer a previously downloaded signed bundle from trusted local media.
7. **Wi-Fi later, not never.** Once device support is verified, normal Wi-Fi setup is simple and follows the same saved-network privacy rules as the rest of UniversalOS.
8. **Clear failures.** Unsupported hardware, missing Wi-Fi support, captive portals, low power, or insufficient storage show a recoverable explanation rather than a hanging spinner.

## Cellular reality

Cellular is useful for a completed supported device, but it is not a safe initial bootstrap assumption. It depends on device-specific modem firmware, radio drivers, APN/carrier behavior, SIM/eSIM handling, regulatory obligations, and emergency-call testing. UniversalOS v0 therefore uses USB/Wi-Fi/offline paths first and does not make any cellular promise until a profile has proof.

## What data the device needs

| Stage | Required data | Where it comes from |
| --- | --- | --- |
| Initial boot | Bootstrap Capsule, embedded root metadata | selected locally by Installer/recovery path |
| Local identity | measured board/SoC/ABI/partition facts | device itself |
| Profile decision | signed profiles catalog | embedded/cache, USB transfer, Wi-Fi mirror, or offline bundle |
| System decision | signed targets metadata and manifests | same safe transport choices |
| Full system | core payload + exact device-support payload set | USB installer, Wi-Fi mirror, or offline bundle |
| Ongoing updates | newer signed metadata and matching payload deltas/full artifacts | normal Wi-Fi/cellular/offline after support is established |

## Out of scope until later

```text
Internet-first boot with no local recovery path
Cellular-first installation
Auto-joining unknown Wi-Fi networks
Cloud account required for setup
Executing server-provided driver code before local verification
Silent background download on limited mobile data
```
