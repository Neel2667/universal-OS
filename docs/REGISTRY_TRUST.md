# Signed registry metadata and trust-root reference

## Scope

UniversalOS needs a cloud registry to distribute candidate Bootstrap Capsules, device-support packages, and full core releases. The registry is never trusted merely because it is online. The device must verify signed, expiring metadata locally before it resolves or stages a candidate.

This repository now implements a host-side **Ed25519 metadata verifier** for that trust boundary. It is a reference component for registry metadata—not an on-device key-management system, payload downloader, or flasher.

## Implemented contracts

| Path | Purpose |
| --- | --- |
| `specs/repository-metadata/envelope-v1.json` | Canonical signed metadata envelope: role, version, expiry, signed body, and signatures. |
| `specs/repository-metadata/root-v1.json` | Signed root body: public Ed25519 keys and threshold role definitions. |
| `core/universal_core/registry.py` | Canonical JSON, Ed25519 verification, role thresholds, metadata expiry, rollback protection, and dual-threshold root rotation. |
| `tests/test_registry.py` | Ephemeral-key tests; no private test key or production key is stored in Git. |

The `cryptography` dependency is pinned to the tested major/minor range in `pyproject.toml`. It provides the maintained Ed25519 implementation; UniversalOS does not implement cryptographic primitives itself.

## Metadata roles

| Role | Intended responsibility |
| --- | --- |
| `root` | Defines trusted public keys, role membership, and signature thresholds. |
| `bootstrap` | Authorizes Bootstrap Capsule registry targets. |
| `targets` | Authorizes core-system and device-support registry targets. |

All envelopes contain a positive version and an expiry. `MetadataState` records accepted role versions and rejects a validly signed older version, preventing basic metadata rollback/replay.

## Verification sequence

```text
embedded trusted root
  → verify root is unexpired
  → select expected role and threshold
  → canonicalize envelope without signatures
  → verify distinct Ed25519 signatures
  → reject expired or wrong-role metadata
  → reject versions not newer than locally accepted version
  → expose verified target metadata to compatibility resolver
```

A root rotation requires both:

1. the **current** root's `root` threshold to authorize the candidate; and
2. the **candidate** root's own `root` threshold to authorize itself.

The candidate root version must be greater than the current root version.

## Explicit limitations and safety rules

- Verified `targets` metadata is now bound to exact package-manifest and payload bytes in [Verified target binding and safe installation model](SAFE_INSTALLATION.md). A downloader/staging store and persistent write path remain future work.
- It does not manage production private keys. Production keys must be offline/hardware-backed according to a separately reviewed key ceremony; they must never enter Git, CI, test fixtures, logs, or chat.
- It does not replace a full TUF/Uptane security review. Threshold choice, timestamp/snapshot delegation, mirror behavior, key compromise response, and metadata retention require further design/review.
- It is host-side reference code and does not touch a phone or network.

## Run from a clean environment

```sh
python3 -m venv /tmp/universalos-venv
. /tmp/universalos-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -s tests -v
```

The registry tests create temporary Ed25519 keys in memory. They validate successful signatures, payload tampering, threshold signatures, expiration, metadata rollback, and root rotation.
