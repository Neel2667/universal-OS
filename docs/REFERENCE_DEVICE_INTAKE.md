# Reference-device intake checklist

Use this checklist to provide the facts needed for [issue #3: ADR-001](https://github.com/Neel2667/universal-OS/issues/3). **Do not unlock, flash, relock, root, or erase the phone yet.** The first task is eligibility research and a documented restore path.

## Share these safe details

- Manufacturer and exact marketed model (for example, include the storage/RAM configuration).
- Country/region/carrier variant and purchase year if known.
- Device codename/board name if known; otherwise say "unknown".
- Android version and build number (not account information).
- Whether **Developer options → OEM unlocking** is visible, enabled, disabled, greyed out, or unknown. Do not change it just for this intake.
- Whether the phone is carrier-financed, enterprise-managed, or has any known bootloader restriction.
- Current major hardware condition: display/touch, charging, battery, cameras, Wi-Fi, Bluetooth, cellular, fingerprint, and storage.
- Links to the manufacturer's bootloader-unlock and factory-restore documentation, if you can find them.
- Whether losing local data is acceptable later. A bootloader unlock often performs a factory reset.

## Never post these in an issue, chat, screenshot, or log

- IMEI/MEID, serial number, device ID, MAC addresses, SIM/phone number, Google account identifiers, recovery codes, unlock tokens, authentication cookies, or payment details.
- Full bug reports/logcat dumps before they have been checked for personal data.
- Vendor firmware/proprietary partition images unless their license and redistribution method have been explicitly reviewed.

## Optional, non-destructive identification

If Android Platform Tools/ADB is already installed and USB debugging is enabled on a phone you own, the following commands normally read generic build properties only. Review output before sharing and remove any personal information. Do not run unknown scripts or flashing commands.

```sh
adb shell getprop ro.product.manufacturer
adb shell getprop ro.product.model
adb shell getprop ro.product.device
adb shell getprop ro.product.board
adb shell getprop ro.board.platform
adb shell getprop ro.build.version.release
adb shell getprop ro.build.fingerprint
```

The output helps distinguish a marketing model from the actual board/codename, but it is not sufficient proof that the device is unlockable or maintainable. ADR-001 still requires authoritative unlock/restore, source, firmware, and community-maintenance evidence.

## Eligibility red flags

Pause the target evaluation if any of these apply until they are researched:

- OEM unlocking is absent/greyed out due to carrier or regional policy.
- There is no official factory restore method and no well-documented, community-tested rescue path.
- Kernel source, device tree, or essential firmware provenance is missing or contradictory.
- The device has an irreversible anti-rollback/relock rule that has not been understood.
- The only available instructions require downloading random images/tools from untrusted sources.

An ineligible device is not a failure—it saves the project from an unsafe first port.
