# Arena native build provisioning request

The selected native build target is **Arena**. Provision a container/host capable of building the UniversalOS QEMU ARM64 Discovery Base.

## Required tools

```text
Rust 1.85.0 or newer pinned exact release
Cargo, rustfmt, clippy
Rust targets: aarch64-unknown-linux-gnu, aarch64-unknown-none
Yocto/OpenEmbedded BitBake pinned checkout
QEMU: qemu-system-aarch64 / ARM virt support
GCC/G++/make/cmake and Yocto host dependencies
Git, Python 3, tar/xz/zstd, locales
```

## Validation after provisioning

```sh
python3 tools/check_native_build_host.py --strict
rustc --version
cargo --version
bitbake --version
qemu-system-aarch64 --version
```

## Current blocker

The current Arena host lacks Rust/Cargo/BitBake/QEMU and outbound Rust/Debian package endpoints were unavailable. Do not mark the Discovery Base build as complete until the strict check succeeds.

## Image definition

`native/environment/Containerfile` is a starting specification. Before production use, pin the base image to an immutable digest, pin Yocto layer revisions in `specs/build/lock-v1.json`, and generate an SBOM for the build environment itself.
