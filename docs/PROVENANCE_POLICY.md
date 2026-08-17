# Source, firmware, model, and binary provenance policy

## Purpose

UniversalOS cannot claim long-lived device support if it cannot explain where each source tree, firmware item, binary, model weight, generated artifact, and build input originated. This policy prevents accidental inclusion of unlicensed vendor material, private device data, or unverifiable binaries.

## Rules

1. No vendor firmware, extracted partition image, proprietary blob, private signing key, personal device identifier, or user data enters Git.
2. Every external component used in an image has a v1 provenance record before distribution.
3. A hash establishes exact input identity; it does not establish redistribution rights.
4. `allowed` redistribution for a binary/firmware component requires an approved review state and evidence.
5. `user-extraction-only` means the repository may provide lawful extraction instructions and hash expectations, but not the proprietary payload.
6. `not-allowed` components cannot be included in a public image or mirror.
7. `pending-review` components cannot enter a release image.
8. Source offers, notices, SPDX/license obligations, modifications, and build provenance are release gates.
9. Model weights are treated like binaries: license, terms, size, hash, and redistribution decision are required if the idea is ever reintroduced.

## Record format

`specs/provenance/component-v1.json` defines a non-secret inventory record:

```text
component identity and kind
source URL and revision
license/SPDX and notice requirement
redistribution decision
exact SHA-256 input digest
target architecture/profile scope
review state and evidence
```

`tools/validate_provenance.py` validates only metadata. It does not download, approve, extract, or distribute anything.

## Component categories

| Kind | Typical example | Required treatment |
| --- | --- | --- |
| `source` | Rust crate, kernel source, build recipe | revision, license, source notice, build record |
| `generated` | generated bindings/SBOM | generator version and reproducible input record |
| `binary` | closed library | license and redistribution review before use |
| `firmware` | radio/DSP/Wi-Fi/GPU firmware | strict source, legal, device profile, extraction, and security review |
| `model` | optional local model weight | same binary controls plus model terms and resource policy |

## Release gate

A release candidate is blocked when any included component lacks a source/revision/hash record, has a rejected/pending distribution state, omits required notices, or lacks an accountable review decision.
