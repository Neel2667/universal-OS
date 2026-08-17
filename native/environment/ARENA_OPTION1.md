# Option 1 — Arena native container activation

The repository now contains a Dev Container definition and pinned Yocto source commit for Option 1.

## Arena action required

Instantiate/rebuild the workspace using `.devcontainer/devcontainer.json`, or build `native/environment/Containerfile` with the repository mounted at `/workspace`.

## Expected post-create gate

```sh
verify-universalos-native-env
```

This executes:

```text
Rust/Cargo/rustfmt/clippy check
ARM64 Rust target check
BitBake check
QEMU ARM64 check
UniversalOS host preflight
```

## Current limitation

The active sandbox has no container runtime and its direct Rust/Debian endpoints are blocked, so this definition cannot be built from inside the current shell. The container provisioning service must build/attach it.
