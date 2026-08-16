# Universal Installer and Bootstrap Capsule contracts

## Purpose

This is the second executable, device-neutral UniversalOS prototype slice. It models the safe transition from **preliminary installer discovery** to selection of the smallest compatible **Bootstrap Capsule**.

It does not connect to a phone, collect a real USB identifier, download an image, flash a partition, switch an A/B slot, or reboot anything. All test data is synthetic.

## Contracts

| Path | Purpose |
| --- | --- |
| `specs/discovery-record/schema-v1.json` | Strict, non-personal preliminary facts that an installer/recovery transport may provide. |
| `specs/bootstrap-capsule/schema-v1.json` | Signed metadata for a minimal Discovery Base bootstrap/recovery capsule. |
| `core/universal_core/discovery.py` | Dependency-free parser for discovery records. |
| `core/universal_core/bootstrap.py` | Fail-closed Bootstrap Capsule parser and resolver. |
| `testdata/discovery/` | Synthetic unlocked ARM64/fastboot and ARMv7/recovery discovery records. |
| `testdata/bootstrap_capsules/` | Compatible, older, wrong-board, and rogue test capsule manifests. |
| `tests/test_bootstrap.py` | Unit tests for selection and unsafe/ambiguous failure paths. |

## Safety model

A discovery record is only an input for choosing a small Discovery Base bootstrap. It is **not final hardware trust**. Once Discovery Base starts, it must re-measure the relevant board, SoC, partition, ABI, and capability facts locally before it may request a full UniversalOS installation plan.

The resolver accepts a capsule only when all of these conditions hold:

1. the record confirms an unlocked bootloader;
2. the capsule's test trust metadata is accepted and unexpired;
3. architecture, board family, SoC family, partition model, and permitted transport all match exactly;
4. the capsule declares offline recovery; and
5. there is exactly one newest matching capsule.

The resolver rejects wildcard board/SoC bootstrap manifests. A broad "try this on any phone" bootstrap is unsafe. The portability comes from a shared Discovery Base and reusable family capsules, not from guessing early boot compatibility.

## Test-only trust boundary

The bootstrap selection fixtures still use `FixtureTrustVerifier`, which accepts deterministic markers and cannot authorize an actual capsule. The repository now has a separate Ed25519 threshold metadata reference implementation; see [Signed registry metadata and trust root](REGISTRY_TRUST.md). Binding verified bootstrap targets to downloaded capsule digests and a write path remains a future security gate.

## Run

```sh
python3 tools/validate_contracts.py
python3 -m unittest discover -s tests -v
```

Expected Discovery Base selection includes two structurally different synthetic devices:

```text
uos.discovery.synthetic.cedar-unlocked-v1: bootstrap=uos.bootstrap.synthetic-cedar@0.1.0; rejected=4
uos.discovery.synthetic.orion-unlocked-v1: bootstrap=uos.bootstrap.synthetic-orion@0.1.1; rejected=3
```

The generic profile/package resolver then runs as a separate stage. This separation makes it clear that the installer selects only a minimal bootstrap first; the full UniversalOS core is selected later by locally verified profile facts.
