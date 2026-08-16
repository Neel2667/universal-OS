# Signed test repository laboratory

## Purpose

The secure update architecture now has a self-contained, **non-production** repository laboratory. It creates fresh disposable Ed25519 test keys, signed root/targets metadata, harmless package manifests, and harmless payload bytes outside the Git checkout.

It exists to prove the trust → target → manifest → payload path before a downloader, Bootstrap Capsule, or physical device is involved.

## Safety boundary

```text
TEST-ONLY keys
  → never production keys
  → never committed to Git
  → never uploaded to CI
  → never used for device images
  → never treated as a real trust root
```

The generator refuses to run unless `--i-understand-test-keys` is supplied. It also refuses to write inside the UniversalOS source checkout and writes private test-key files with mode `0600`.

## Run

```sh
python3 -m pip install -e .
python3 tools/generate_test_repository.py \
  /tmp/universalos-test-repository \
  --i-understand-test-keys
```

The generated directory contains:

```text
TEST_ONLY_NOT_FOR_RELEASE.txt
metadata/root.json
metadata/targets.json
keys/test-root-ed25519.raw
keys/test-targets-ed25519.raw
manifests/*.json
artifacts/*.bin
```

All artifacts are harmless text test payloads. The validator verifies Ed25519 metadata thresholds and each target's exact manifest/payload binding.

## Deliberate limits

This is not a release publisher, mirror, package downloader, key ceremony, OTA server, or device installer. Production work requires offline/hardware-backed keys, separate signing roles, expiry/rotation operations, review, artifact provenance, mirrors, persistent device trust state, and QEMU/device recovery proof.
