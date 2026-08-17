#!/usr/bin/env sh
set -eu
cd /workspace
python3 tools/check_native_build_host.py --strict
rustc --version
cargo --version
bitbake --version
qemu-system-aarch64 --version
printf '%s\n' 'UniversalOS native build environment is ready.'
