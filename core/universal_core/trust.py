"""Trust-verifier boundary for the portable resolver prototype.

FixtureTrustVerifier is deliberately NOT cryptography. It validates fixed test
markers, trust membership, and expiry so resolution policy can be tested with
no third-party packages. Production work must replace it with an independently
reviewed threshold-signature and repository-metadata implementation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from .errors import TrustError


class TrustSubject(Protocol):
    """Minimal signed-metadata fields shared by package and bootstrap manifests."""

    signer: str
    signature: str
    expires: datetime


class TrustVerifier(Protocol):
    def verify(self, manifest: TrustSubject, now: datetime) -> None:
        """Raise TrustError unless trusted metadata authorizes this manifest."""


class FixtureTrustVerifier:
    """Deterministic verifier for explicit test-only signatures.

    Valid test signatures have the exact form `fixture:<signer>:trusted`.
    This class must never be connected to an artifact downloader or release
    pipeline, because it offers no cryptographic authenticity.
    """

    def __init__(self, trusted_signers: set[str]) -> None:
        self._trusted_signers = frozenset(trusted_signers)

    def verify(self, manifest: TrustSubject, now: datetime) -> None:
        if now.tzinfo is None:
            raise TrustError("verification time must include a timezone")
        if manifest.signer not in self._trusted_signers:
            raise TrustError(f"untrusted signer: {manifest.signer}")
        if manifest.signature != f"fixture:{manifest.signer}:trusted":
            raise TrustError("fixture signature marker is invalid")
        if manifest.expires <= now.astimezone(timezone.utc):
            raise TrustError("package metadata is expired")
