# UniversalOS UI foundation

UniversalOS uses a workspace-first shell rather than an app-grid-first model. A workspace groups goal-relevant surfaces such as tasks, files, notes, media, communication, system, and recovery.

The current host-side contract provides:

```text
workspace identity and allowed surfaces
workspace switching
recovery mode that blocks normal navigation
accessibility preference parsing
design token schema
```

It does not render a UI yet. Rendering begins after native Discovery Base/QEMU work can host the system shell.
