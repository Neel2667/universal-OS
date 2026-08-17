# Bootstrap adapter, sanitized observation, and recovery proof

These contracts bridge a real device bootloader/recovery path to the common UniversalOS Discovery Base without placing raw commands, serial numbers, or private device output in the core.

```text
approved adapter manifest
+ sanitized boot observation
→ preliminary DiscoveryRecord
→ signed bootstrap/profile catalogs
→ common installer flow
```

The adapter permits only approved product identifiers, architecture, board/SoC family, slot layout, transport, and recovery policy. It rejects wildcard products, locked bootloaders, incompatible slot layouts, and unknown/sensitive observation fields.

A recovery proof records a successful offline restore scenario, exact restore artifact digest, data-loss disclosure, build/profile/adapter identity, and redacted evidence. It is required before a physical device can move above lab status.
