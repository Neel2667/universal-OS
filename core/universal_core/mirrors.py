"""Bounded mirror retrieval for verified UniversalOS artifact transport.

Mirrors provide bytes only. They do not authorize metadata, profiles, capsules,
or payloads; callers must pass retrieved bytes through the local trust pipeline.
"""
from __future__ import annotations

import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable

from .errors import TrustError


@dataclass(frozen=True)
class MirrorEndpoint:
    base_url: str
    priority: int = 100

    def normalized(self, *, allow_file_for_test: bool = False) -> str:
        parsed = urllib.parse.urlparse(self.base_url)
        allowed = {"https"}
        if allow_file_for_test:
            allowed.add("file")
        if parsed.scheme not in allowed or not parsed.netloc and parsed.scheme != "file":
            raise TrustError("mirror endpoint must use approved transport")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise TrustError("mirror endpoint contains unsafe authority/query fields")
        return self.base_url.rstrip("/") + "/"


@dataclass(frozen=True)
class MirrorFetch:
    endpoint: str
    relative_path: str
    data: bytes


def _safe_relative_path(value: str) -> str:
    if not value or value.startswith("/") or "\\" in value:
        raise TrustError("mirror path must be a non-empty relative slash path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise TrustError("mirror path contains unsafe traversal")
    return value


def fetch_from_mirrors(
    endpoints: Iterable[MirrorEndpoint],
    relative_path: str,
    *,
    max_bytes: int,
    timeout_seconds: float = 15.0,
    allow_file_for_test: bool = False,
) -> MirrorFetch:
    """Fetch bounded bytes from prioritized mirrors, without trusting content."""
    if max_bytes < 1:
        raise TrustError("mirror fetch max_bytes must be positive")
    path = _safe_relative_path(relative_path)
    errors: list[str] = []
    ordered = sorted(endpoints, key=lambda endpoint: endpoint.priority)
    if not ordered:
        raise TrustError("no mirror endpoints configured")
    for endpoint in ordered:
        try:
            base = endpoint.normalized(allow_file_for_test=allow_file_for_test)
            url = urllib.parse.urljoin(base, path)
            if not url.startswith(base):
                raise TrustError("mirror path escaped configured base")
            request = urllib.request.Request(url, headers={"User-Agent": "UniversalOS-Discovery/0.1"})
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # nosec B310: scheme policy checked above
                length = response.headers.get("Content-Length")
                if length is not None and int(length) > max_bytes:
                    raise TrustError("mirror response exceeds configured size limit")
                data = response.read(max_bytes + 1)
                if len(data) > max_bytes:
                    raise TrustError("mirror response exceeds configured size limit")
                return MirrorFetch(base, path, data)
        except (OSError, ValueError, urllib.error.URLError, TrustError) as exc:
            errors.append(type(exc).__name__)
    raise TrustError("all configured mirrors failed: " + ",".join(errors))
