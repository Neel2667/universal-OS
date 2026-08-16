"""UniversalOS portable core reference contracts.

This package is a host-side policy prototype, not a kernel, boot image, driver,
or production update client. It has no device-name logic and is intentionally
limited to parsing and resolving declarative compatibility metadata.
"""

from .bootstrap import BootstrapPlan, select_bootstrap
from .discovery import DiscoveryRecord
from .errors import ContractError, PersistenceError, ResolutionError, TrustError
from .health import HealthPolicy, HealthReport, health_is_confirmed
from .install import InstallJournal, InstallState
from .preflight import DeviceConditions, PreflightPolicy, evaluate_preflight
from .registry import MetadataState, SignedMetadata, TrustRoot, rotate_root, verify_and_accept, verify_metadata
from .resolver import ResolutionPlan, resolve, resolve_verified_manifests
from .services import DeviceStatus, RecoveryReport, StagedUpdate, UniversalSystemServices, UpdateBlockedError
from .trust import FixtureTrustVerifier

__all__ = [
    "BootstrapPlan",
    "ContractError",
    "DeviceConditions",
    "DeviceStatus",
    "HealthPolicy",
    "HealthReport",
    "InstallJournal",
    "InstallState",
    "DiscoveryRecord",
    "FixtureTrustVerifier",
    "MetadataState",
    "PersistenceError",
    "PreflightPolicy",
    "ResolutionError",
    "RecoveryReport",
    "ResolutionPlan",
    "StagedUpdate",
    "SignedMetadata",
    "TrustRoot",
    "UniversalSystemServices",
    "UpdateBlockedError",
    "TrustError",
    "evaluate_preflight",
    "health_is_confirmed",
    "resolve",
    "resolve_verified_manifests",
    "select_bootstrap",
    "rotate_root",
    "verify_and_accept",
    "verify_metadata",
]
