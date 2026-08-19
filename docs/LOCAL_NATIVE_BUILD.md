# Local native build path

When Arena cannot instantiate the native Dev Container, a developer-controlled Linux computer with Docker or Podman is the supported fallback.

## Prerequisites

```text
Linux host
Docker or Podman
Git
internet access for the first container build
sufficient disk space for Yocto source/build caches
```

No phone, USB cable, fastboot, ADB, firmware, or device credentials are required for this QEMU/native stage.

## One-command workflow

```sh
git clone -b arena/01a00b34-universal-os \
  https://github.com/Neel2667/universal-OS.git
cd universal-OS

tools/run_native_container.sh build
tools/run_native_container.sh verify
tools/run_native_container.sh rust-test
```

To inspect the environment:

```sh
tools/run_native_container.sh shell
```

For Podman:

```sh
CONTAINER_RUNTIME=podman tools/run_native_container.sh build
```

## What the script does

| Command | Effect |
| --- | --- |
| `build` | Builds the Rust/Yocto/QEMU image from `native/environment/Containerfile`. |
| `verify` | Runs the strict native host preflight inside the container. |
| `rust-test` | Formats, lints, tests, builds release binaries, and cross-builds native contracts for ARM64. |
| `shell` | Opens a container shell with the repository mounted at `/workspace`. |

The source checkout is mounted into the container. Build outputs remain local to the host/container setup and must not be committed unless a reviewed release process explicitly requires them.

## Security rule

The container is a build environment, not a signing environment. Production private keys, vendor firmware, user device images, and personal data must never be copied into it.
