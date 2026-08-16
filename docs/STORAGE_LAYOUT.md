# Safe storage layout contract

`specs/storage/layout-v1.json` makes the immutable safety requirement explicit.

```text
A/B:             known-good slot A or B + different inactive staging slot
Transactional:   known-good generation + separate next transaction generation
Single-slot:     normal full-system update rejected; recovery-only design required
```

Every layout requires an offline recovery route. No normal updater may overwrite the known-good target in place.
