# UniversalOS Device Enablement Kit

A device port contributes a **small enablement manifest**, Bootstrap Capsule, signed profile match, provenance records, and recovery evidence. It must not fork the UniversalOS core/UI.

The v1 manifest records the profile, selected bootstrap capsule, support tier, offline recovery availability, feature status, and provenance-component IDs.

Admission sequence:

```text
local facts match signed profile
→ signed Bootstrap Capsule catalog match
→ source/firmware provenance review
→ offline recovery test
→ feature matrix evidence
→ update/rollback test
→ support tier decision
```

`profiled` and `lab` never imply public user support. `verified` requires real install/update/rollback/recovery evidence. `maintained` additionally requires active security ownership and regular regression evidence.
