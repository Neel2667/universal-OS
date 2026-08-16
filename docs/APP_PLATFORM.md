# UniversalOS application platform

UniversalOS must not let applications bypass the core updater, profile service, recovery, device enablement, or health authority.

## Application classes

| Class | Intended use | Trust level |
| --- | --- | --- |
| `native-system` | Discovery Base, update, health, recovery, shell services | system signer only |
| `wasi-component` | future portable third-party applications | sandboxed, explicit scoped capabilities |

## Capability rules

Apps may request only user-facing capabilities such as selected-file access, user-approved writes, camera, microphone, location, network, notifications, and sharing. A request does not grant authority. The system issues a time-bounded grant after user approval.

Apps cannot request:

```text
update staging
health reporting
recovery control
Bootstrap Capsule selection
profile selection
raw device driver access
system signing
```

The current module validates manifests and grants; it does not embed a Wasm runtime yet. A native runtime is blocked with the Discovery Base toolchain work.
