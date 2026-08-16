# Reproducible build and CI runbook

A future native Discovery Base build must use a checked build lock with source revision, Rust toolchain digest, Yocto revision digest, target, and every external input revision/hash. `tools/validate_build_lock.py` validates the record shape before a build is described as reproducible.

GitHub CI workflow files remain blocked by the current integration's missing workflow permission. Until that permission is available, the required local gate is:

```sh
python tools/check_native_build_host.py
python tools/validate_contracts.py
python tools/validate_provenance.py
python tools/validate_device_enablement.py
python tools/validate_device_matrix.py
python tools/validate_build_lock.py
python -m unittest discover -s tests -v
```

Once native tooling is available, these commands become a required CI job before QEMU/image work.
