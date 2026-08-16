"""UniversalOS portable core reference contracts.

This package is a host-side policy prototype, not a kernel, boot image, driver,
or production update client. It has no device-name logic and is intentionally
limited to parsing and resolving declarative compatibility metadata.
"""

from .bootstrap import BootstrapPlan, select_bootstrap
from .discovery import DiscoveryRecord
from .errors import ContractError, ResolutionError, TrustError
from .resolver import ResolutionPlan, resolve
from .trust import FixtureTrustVerifier

__all__ = [
    "BootstrapPlan",
    "ContractError",
    "DiscoveryRecord",
    "FixtureTrustVerifier",
    "ResolutionError",
    "ResolutionPlan",
    "TrustError",
    "resolve",
    "select_bootstrap",
]
