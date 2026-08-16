# UniversalOS offline bundle path

A phone must be installable without phone internet. An offline bundle is a copied signed repository layout containing root/role metadata, manifests, and payload artifacts. The normal verifier treats it like any other untrusted transport source: it still checks signatures, profile match, manifest hashes, payload hashes, and installation safety.

```text
Any computer downloads bundle
  → user transfers bundle by USB/removable media
  → Discovery Base verifies locally
  → only matching verified artifacts can stage
```

The current helper verifies only the **test-only** repository laboratory:

```sh
python3 tools/verify_offline_bundle.py /path/to/test-repository
```

Production offline bundles require a future signed bundle index, production key ceremony, legal/provenance review, persistent device trust state, and a native transfer adapter. No production key or artifact is included in this repository.
