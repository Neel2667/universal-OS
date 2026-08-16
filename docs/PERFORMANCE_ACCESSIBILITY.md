# UniversalOS performance and accessibility budgets

## Measurement rule

“Fast” is not accepted as a visual claim. Every budget is measured per hardware tier with exact build, profile, power state, thermal state, test procedure, and repetitions recorded.

## Initial performance budgets

These are engineering budgets for v0.1 planning, not public promises until measured on QEMU and hardware.

| Area | Budget rule |
| --- | --- |
| Discovery Base | no network dependency on critical boot/recovery path |
| Idle work | no continuous polling service without explicit purpose/measurement |
| Update check | bounded metadata transfer, resumable, no full artifact download without policy/user approval |
| Transfer | chunked/resumable; verify incrementally and final digest |
| Memory | core services publish RSS/heap baseline per profile; regressions require issue/evidence |
| UI | key system interactions report input-to-frame timing; no decorative animation in recovery path |
| Battery/thermal | update/inference-like work defers when thermal/power policy blocks it |
| Storage | staging reserve is checked before transfer/install; never fill the only recovery space |

## Accessibility baseline

```text
scalable text
high-contrast mode
screen-reader labels for every system action
keyboard/switch navigation where hardware permits
reduced-motion mode
non-color-only status indicators
large recovery controls
physical-button fallback where touch is unavailable
```

Accessibility is part of the device feature matrix and release evidence, not a post-launch enhancement.
