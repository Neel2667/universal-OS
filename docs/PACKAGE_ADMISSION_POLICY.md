# Package admission policy

A package can enter staging only after all local gates pass:

```text
verified signed role metadata
exact target descriptor
manifest hash and payload hash
exact hardware profile/architecture/kernel ABI/capabilities
bootstrap version range
partition-model compatibility
power/storage/offline-recovery preflight
provenance and license state
```

A package is rejected—not deferred as a hidden background retry—when it is unknown, expired, rollbacked, mismatched, unprovenanced, tampered, or cannot fit safely. The UI receives a bounded reason code and a recovery path.
