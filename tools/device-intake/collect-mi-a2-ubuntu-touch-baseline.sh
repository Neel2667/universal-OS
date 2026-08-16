#!/usr/bin/env sh
# Collect a deliberately limited, read-only baseline from a Xiaomi Mi A2 running Ubuntu Touch.
# Run this only on the owner's own computer, after reading docs/DEVICE_EVALUATIONS/xiaomi-mi-a2-jasmine-sprout.md.
# It does not unlock, reboot, erase, install, flash, mount read-write, or send data over the network.
# Review the output before sharing it: do not publish unique identifiers, account details, IP addresses, or full logs.

set -eu

if [ "${1:-}" != "--consent-read-only" ]; then
  cat >&2 <<'USAGE'
Usage: collect-mi-a2-ubuntu-touch-baseline.sh --consent-read-only > mi-a2-baseline.txt

This script only asks ADB for selected system identity, OS, kernel, partition-label,
and storage information. It does not change the phone. Review mi-a2-baseline.txt before
sharing it and remove any information you do not want to disclose.
USAGE
  exit 64
fi

ADB="${ADB:-adb}"
if ! command -v "$ADB" >/dev/null 2>&1; then
  echo "ERROR: adb was not found. Install Android Platform Tools, enable the appropriate USB/ADB developer access in Ubuntu Touch, then retry." >&2
  exit 127
fi

if ! "$ADB" get-state >/dev/null 2>&1; then
  cat >&2 <<'ERROR'
ERROR: No authorized ADB device was found.

Do not switch to fastboot or install any tool just for this collection. Check the Ubuntu Touch developer/USB settings and cable first. This script may also be skipped; the project can proceed with manual device details.
ERROR
  exit 1
fi

"$ADB" shell 'sh -s' <<'REMOTE'
echo "# UniversalOS read-only Mi A2 / Ubuntu Touch baseline"
echo "# Collected locally; inspect before sharing."
echo

echo "## Operating system"
if [ -r /etc/os-release ]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  printf "NAME=%s\nVERSION=%s\nVERSION_ID=%s\n" "${NAME:-unknown}" "${VERSION:-unknown}" "${VERSION_ID:-unknown}"
else
  echo "os-release unavailable"
fi
uname -a 2>/dev/null || true
printf "kernel-release="
uname -r 2>/dev/null || true
echo

echo "## Generic Android/board properties (serial and radio identifiers deliberately omitted)"
if command -v getprop >/dev/null 2>&1; then
  for p in \
    ro.product.manufacturer \
    ro.product.model \
    ro.product.device \
    ro.product.board \
    ro.board.platform \
    ro.build.version.release \
    ro.build.fingerprint \
    ro.boot.slot_suffix \
    ro.boot.slot; do
    value="$(getprop "$p" 2>/dev/null || true)"
    [ -n "$value" ] && printf "%s=%s\n" "$p" "$value"
  done
else
  echo "getprop unavailable in current Ubuntu Touch shell"
fi
echo

echo "## Boot and partition labels (names only)"
if [ -r /proc/cmdline ]; then
  cat /proc/cmdline
else
  echo "kernel command line unavailable"
fi
if [ -d /dev/disk/by-partlabel ]; then
  find /dev/disk/by-partlabel -maxdepth 1 -mindepth 1 -printf "%f\n" 2>/dev/null | sort
else
  echo "partition-label directory unavailable"
fi
echo

echo "## Storage summary"
df -h 2>/dev/null || true
if [ -r /proc/partitions ]; then
  cat /proc/partitions
fi
REMOTE
