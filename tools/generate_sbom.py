#!/usr/bin/env python3
"""Generate a deterministic SPDX-lite SBOM from approved provenance metadata."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from validate_provenance import ProvenanceRecord
ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--created-at", required=True, help="ISO-8601 timestamp supplied by reproducible release tooling")
    args = parser.parse_args()
    packages=[]
    for path in sorted((ROOT / "testdata/provenance").glob("*.json")):
        raw=json.loads(path.read_text())
        item=ProvenanceRecord.from_dict(raw)
        packages.append({"SPDXID":"SPDXRef-"+item.component_id.replace(".","-"),"name":item.component_id,"versionInfo":raw["version"],"downloadLocation":raw["origin"]["url"],"licenseConcluded":raw["license"]["spdx"],"checksums":[{"algorithm":"SHA256","checksumValue":item.sha256}],"filesAnalyzed":False,"comment":"redistribution="+item.redistribution+"; review="+item.review_state})
    sbom={"spdxVersion":"SPDX-2.3","dataLicense":"CC0-1.0","SPDXID":"SPDXRef-DOCUMENT","name":"UniversalOS-Reference-SBOM","documentNamespace":"https://universalos.dev/sbom/reference/"+args.created_at,"creationInfo":{"created":args.created_at,"creators":["Tool: UniversalOS generate_sbom.py"]},"packages":packages}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(sbom,sort_keys=True,indent=2)+"\n")
    print(f"Wrote SPDX-lite SBOM with {len(packages)} component(s): {args.output}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
