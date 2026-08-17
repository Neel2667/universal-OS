# UniversalOS USB and offline resumable transfer protocol

## Purpose

The first installation path must work even before phone Wi-Fi/cellular support exists. This transport model lets a Universal Installer, offline bundle reader, or future USB recovery gadget transfer signed artifacts in resumable chunks.

```text
verified target descriptor
  → transport manifest bound to descriptor
  → chunk digest checks
  → persistent received-chunk journal
  → full payload digest check
  → completed artifact
  → manifest/payload verifier and staging service
```

## Security boundary

A transfer manifest is **not** a signature and is not permission to install code. It is accepted only after binding to a target already present in verified signed targets metadata. Chunk hashes make disconnect/resume corruption detectable; full completed bytes are checked again against the signed target digest.

## Components

| Path | Purpose |
| --- | --- |
| `specs/transfer/manifest-v1.json` | Transport-only artifact and chunk map. |
| `core/universal_core/transfer.py` | Descriptor binding, resumable chunk receiver, persistent journal, final digest check. |
| `tests/test_transfer.py` | Resume, missing-chunk, tamper, and unknown-target tests. |

## USB stages

```text
Stage 0 — device-specific approved bootloader/recovery transport
  → transfers selected Bootstrap Capsule / Discovery Base

Stage 1 — common UniversalOS Discovery Base USB transfer service
  → transfers profiles metadata, targets metadata, manifests, and payloads

Stage 2 — normal device network/offline update paths
  → uses same verified artifact pipeline
```

Stage 0 differs by bootloader family. Stage 1 is the UniversalOS common transport after the Discovery Base has started.

## Resume behavior

- Received chunks are written at fixed offsets after chunk-digest validation.
- A journal stores only transfer identity and received indexes, never personal device data.
- Restarting with the same transfer manifest resumes missing chunks.
- An altered manifest under the same transfer ID is rejected.
- A final full SHA-256 check happens before the artifact is marked complete.
- Missing chunks, wrong chunk length, wrong digest, wrong target ID, or descriptor mismatch stop the transfer safely.

## Limits

This is a host-side file model, not an actual USB gadget driver or bootloader client. It does not open a device, invoke fastboot/ADB, download over the network, or flash a partition. The native Discovery Base later implements the same semantics over its local USB transport.
