# UniversalOS native workspace

This workspace is the first native Rust migration target. It is intentionally small and dependency-free:

```text
uos-contracts
  allocation-free no_std Bootstrap Capsule selection contract

uos-discoveryd
  host/QEMU smoke-test service scaffold
```

## Status

Source scaffold is committed, but the current Arena environment has no Rust/Cargo/Yocto/QEMU toolchain. It is **not claimed compiled** here yet.

Once the Arena provisioning request is satisfied:

```sh
cd native
cargo fmt --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo build --workspace --release
cargo build -p uos-contracts --target aarch64-unknown-none
```

The Python reference implementation remains the behavioral oracle until these native tests pass and are compared against it.
