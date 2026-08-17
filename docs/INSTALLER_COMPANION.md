# UniversalOS USB Installer companion

The computer-side Universal Installer is a **planner and transport companion**, not the trust root and not an unrestricted flashing tool.

## Five safety responsibilities

1. Load an approved Bootstrap Adapter manifest.
2. Consume only sanitized local boot observations.
3. Produce a dry-run plan before any transfer.
4. Require explicit data-loss acknowledgement before Bootstrap Capsule transfer.
5. Show an offline/factory recovery path in every plan.

The current CLI is non-executing:

```sh
python tools/plan_usb_install.py \
  --adapter testdata/bootstrap-adapter/synthetic-orion.json \
  --observation testdata/installer/synthetic-orion-observation.json
```

Add `--acknowledge-data-loss` only to demonstrate the next planned state. The tool does not open USB, fastboot, ADB, network, or device partitions.

A future native installer must still ensure the phone independently verifies signed Bootstrap/profile/target metadata and every artifact after transfer.
