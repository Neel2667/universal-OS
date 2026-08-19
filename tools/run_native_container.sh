#!/usr/bin/env sh
# Run the UniversalOS native build environment on a developer-controlled host.
# This script never opens USB/fastboot/ADB or touches a physical phone.
set -eu

usage() {
  cat <<'USAGE'
Usage: tools/run_native_container.sh <build|verify|shell|rust-test>

Environment:
  CONTAINER_RUNTIME=docker|podman  (default: docker)
  UOS_NATIVE_IMAGE=tag             (default: universalos-native:dev)

Commands:
  build      Build the pinned native environment image.
  verify     Run the container's native host preflight.
  shell      Open a shell in the container with the repository mounted.
  rust-test  Run format, clippy, native tests, release build, and ARM64 contract build.
USAGE
}

[ "$#" -eq 1 ] || { usage >&2; exit 64; }
COMMAND="$1"
RUNTIME="${CONTAINER_RUNTIME:-docker}"
IMAGE="${UOS_NATIVE_IMAGE:-universalos-native:dev}"

command -v "$RUNTIME" >/dev/null 2>&1 || {
  printf 'Container runtime not found: %s\n' "$RUNTIME" >&2
  printf 'Install Docker or Podman, then retry.\n' >&2
  exit 127
}

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

case "$COMMAND" in
  build)
    exec "$RUNTIME" build -f "$ROOT/native/environment/Containerfile" -t "$IMAGE" "$ROOT"
    ;;
  verify)
    exec "$RUNTIME" run --rm -v "$ROOT:/workspace" -w /workspace "$IMAGE" verify-universalos-native-env
    ;;
  shell)
    exec "$RUNTIME" run --rm -it -v "$ROOT:/workspace" -w /workspace "$IMAGE" bash
    ;;
  rust-test)
    exec "$RUNTIME" run --rm -v "$ROOT:/workspace" -w /workspace/native "$IMAGE" sh -ceu '
      cargo fmt --check
      cargo clippy --workspace --all-targets -- -D warnings
      cargo test --workspace
      cargo build --workspace --release
      cargo build -p uos-contracts --target aarch64-unknown-none
    '
    ;;
  *)
    usage >&2
    exit 64
    ;;
esac
