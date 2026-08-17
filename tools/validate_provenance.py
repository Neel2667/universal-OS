#!/usr/bin/env python3
"""Validate non-secret UniversalOS component provenance records.

This tool intentionally validates metadata only. It neither downloads source nor
firmware, extracts device partitions, accepts licenses, or redistributes any
binary. Legal review remains a human decision recorded in each entry.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURES = frozenset({"arm64", "armv7", "x86_64", "riscv64"})


class ProvenanceError(ValueError):
    """A provenance record is malformed or unsafe to treat as reviewed."""


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ProvenanceError(f"{name} must be an object")
    return value


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProvenanceError(f"{name} must be a non-empty string")
    return value


def _keys(value: Mapping[str, Any], name: str, required: frozenset[str], allowed: frozenset[str]) -> None:
    missing = required - value.keys()
    unknown = value.keys() - allowed
    if missing:
        raise ProvenanceError(f"{name} missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ProvenanceError(f"{name} has unknown fields: {', '.join(sorted(unknown))}")


@dataclass(frozen=True)
class ProvenanceRecord:
    component_id: str
    kind: str
    redistribution: str
    review_state: str
    sha256: str

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ProvenanceRecord":
        _keys(
            raw,
            "provenance",
            frozenset({"schema_version", "component_id", "kind", "version", "origin", "license", "redistribution", "integrity", "review"}),
            frozenset({"schema_version", "component_id", "kind", "version", "origin", "license", "redistribution", "integrity", "targets", "review"}),
        )
        if raw["schema_version"] != 1:
            raise ProvenanceError("provenance schema_version must be 1")
        component_id = _string(raw["component_id"], "provenance.component_id")
        if not re.fullmatch(r"uos\.[a-z0-9][a-z0-9._-]*", component_id):
            raise ProvenanceError("provenance.component_id is invalid")
        kind = _string(raw["kind"], "provenance.kind")
        if kind not in {"source", "generated", "binary", "firmware", "model"}:
            raise ProvenanceError("provenance.kind is invalid")
        _string(raw["version"], "provenance.version")

        origin = _mapping(raw["origin"], "provenance.origin")
        _keys(origin, "provenance.origin", frozenset({"url", "revision"}), frozenset({"url", "revision"}))
        origin_url = _string(origin["url"], "provenance.origin.url")
        if urlparse(origin_url).scheme not in {"https", "http", "git", "ssh"}:
            raise ProvenanceError("provenance.origin.url must use a reviewable source URL")
        _string(origin["revision"], "provenance.origin.revision")

        license_info = _mapping(raw["license"], "provenance.license")
        _keys(license_info, "provenance.license", frozenset({"spdx", "notice_required"}), frozenset({"spdx", "notice_required"}))
        _string(license_info["spdx"], "provenance.license.spdx")
        if not isinstance(license_info["notice_required"], bool):
            raise ProvenanceError("provenance.license.notice_required must be boolean")

        redistribution = _string(raw["redistribution"], "provenance.redistribution")
        if redistribution not in {"allowed", "user-extraction-only", "not-allowed", "pending-review"}:
            raise ProvenanceError("provenance.redistribution is invalid")
        integrity = _mapping(raw["integrity"], "provenance.integrity")
        _keys(integrity, "provenance.integrity", frozenset({"sha256"}), frozenset({"sha256"}))
        digest = _string(integrity["sha256"], "provenance.integrity.sha256")
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ProvenanceError("provenance.integrity.sha256 is invalid")

        if "targets" in raw:
            targets = _mapping(raw["targets"], "provenance.targets")
            _keys(targets, "provenance.targets", frozenset(), frozenset({"architectures", "profile_ids"}))
            if "architectures" in targets:
                architectures = targets["architectures"]
                if not isinstance(architectures, list) or not set(architectures) <= ARCHITECTURES:
                    raise ProvenanceError("provenance.targets.architectures is invalid")
            if "profile_ids" in targets:
                profiles = targets["profile_ids"]
                if not isinstance(profiles, list) or any(not isinstance(item, str) or not item for item in profiles):
                    raise ProvenanceError("provenance.targets.profile_ids is invalid")

        review = _mapping(raw["review"], "provenance.review")
        _keys(review, "provenance.review", frozenset({"state", "evidence"}), frozenset({"state", "evidence"}))
        review_state = _string(review["state"], "provenance.review.state")
        if review_state not in {"unreviewed", "approved", "rejected", "needs-legal-review"}:
            raise ProvenanceError("provenance.review.state is invalid")
        _string(review["evidence"], "provenance.review.evidence")

        if kind in {"firmware", "binary"} and redistribution == "allowed" and review_state != "approved":
            raise ProvenanceError("redistributable firmware/binary requires approved review state")
        return cls(component_id, kind, redistribution, review_state, digest)


def main() -> int:
    records = []
    for path in sorted((ROOT / "testdata/provenance").glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            records.append(ProvenanceRecord.from_dict(json.load(handle)))
    print(f"Validated {len(records)} provenance record(s): " + ", ".join(record.component_id for record in records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
