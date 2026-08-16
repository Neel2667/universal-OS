"""Errors used by the portable core contract prototype."""


class ContractError(ValueError):
    """A profile or package does not satisfy the v1 contract."""


class TrustError(ValueError):
    """Fixture trust verification rejected package metadata."""


class ResolutionError(RuntimeError):
    """No safe, compatible resolution plan could be created."""


class PersistenceError(RuntimeError):
    """A staged artifact or persistent installation journal failed integrity checks."""
