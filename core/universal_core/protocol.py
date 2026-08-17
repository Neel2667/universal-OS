"""Transport-independent local service protocol reference.

This is a strict host-side dispatcher for service contracts. CallerContext is
provided by a future native transport after it has authenticated a local peer
through platform credentials/labels. It is not a network API and does not parse
or trust bearer tokens supplied by applications.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .errors import ContractError
from .health import HealthReport
from .services import UniversalSystemServices

CAPABILITIES = frozenset(
    {
        "uos.device.read",
        "uos.update.read",
        "uos.update.request-first-boot",
        "uos.health.report",
        "uos.recovery.read",
    }
)

_METHOD_CAPABILITIES = {
    ("device", "get-status"): "uos.device.read",
    ("update", "get-status"): "uos.update.read",
    ("update", "request-first-boot"): "uos.update.request-first-boot",
    ("health", "report"): "uos.health.report",
    ("recovery", "get-report"): "uos.recovery.read",
}


@dataclass(frozen=True)
class CallerContext:
    """Authenticated local principal supplied by the future platform transport."""

    principal: str
    capabilities: frozenset[str]

    def __post_init__(self) -> None:
        if not self.principal:
            raise ContractError("caller principal must not be empty")
        if not self.capabilities <= CAPABILITIES:
            raise ContractError("caller has an unknown service capability")


@dataclass(frozen=True)
class ServiceRequest:
    request_id: str
    service: str
    method: str
    params: Mapping[str, Any]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ServiceRequest":
        expected = {"schema_version", "request_id", "service", "method", "params"}
        if set(raw) != expected or raw.get("schema_version") != 1:
            raise ContractError("invalid service request envelope")
        request_id = raw["request_id"]
        service = raw["service"]
        method = raw["method"]
        params = raw["params"]
        if not all(isinstance(item, str) and item for item in (request_id, service, method)):
            raise ContractError("service request identity fields must be non-empty strings")
        if not isinstance(params, dict):
            raise ContractError("service request params must be an object")
        return cls(request_id, service, method, dict(params))


@dataclass(frozen=True)
class ServiceResponse:
    request_id: str
    ok: bool
    result: Mapping[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None

    @classmethod
    def success(cls, request_id: str, result: Mapping[str, Any]) -> "ServiceResponse":
        return cls(request_id, True, dict(result))

    @classmethod
    def failure(cls, request_id: str, code: str, message: str) -> "ServiceResponse":
        return cls(request_id, False, None, code, message[:240])

    def to_dict(self) -> dict[str, Any]:
        base: dict[str, Any] = {"schema_version": 1, "request_id": self.request_id, "ok": self.ok}
        if self.ok:
            base["result"] = dict(self.result or {})
        else:
            base["error"] = {"code": self.error_code or "service.internal", "message": self.error_message or "request failed"}
        return base


class LocalServiceGateway:
    """Maps capability-checked local requests to portable system services."""

    def __init__(self, services: UniversalSystemServices) -> None:
        self.services = services

    def dispatch(self, caller: CallerContext, request: ServiceRequest, *, now: datetime | None = None) -> ServiceResponse:
        required = _METHOD_CAPABILITIES.get((request.service, request.method))
        if required is None:
            return ServiceResponse.failure(request.request_id, "service.not-found", "unknown service method")
        if required not in caller.capabilities:
            return ServiceResponse.failure(request.request_id, "service.permission-denied", "caller lacks required capability")
        timestamp = now or datetime.now(timezone.utc)
        try:
            if request.service == "device":
                self._require_empty_params(request)
                status = self.services.status()
                return ServiceResponse.success(
                    request.request_id,
                    {
                        "profile_id": status.profile_id,
                        "support_tier": status.support_tier,
                        "architecture": status.architecture,
                        "partition_model": status.partition_model,
                        "capabilities": dict(status.capabilities),
                        "active_target": status.active_target,
                        "update_state": status.update_state,
                    },
                )
            if request.service == "update" and request.method == "get-status":
                self._require_empty_params(request)
                status = self.services.status()
                return ServiceResponse.success(request.request_id, {"active_target": status.active_target, "update_state": status.update_state})
            if request.service == "update" and request.method == "request-first-boot":
                self._require_empty_params(request)
                journal = self.services.request_first_boot()
                return ServiceResponse.success(request.request_id, {"update_state": journal.state.value, "staged_target": journal.staged_target})
            if request.service == "health":
                report = self._health_report(request.params)
                journal = self.services.confirm_first_boot(report, now=timestamp)
                return ServiceResponse.success(request.request_id, {"update_state": journal.state.value, "active_target": journal.active_target})
            if request.service == "recovery":
                self._require_empty_params(request)
                return ServiceResponse.success(request.request_id, self.services.recovery_report().to_json_dict())
            return ServiceResponse.failure(request.request_id, "service.not-found", "unknown service method")
        except (ContractError, ValueError) as exc:
            return ServiceResponse.failure(request.request_id, "service.invalid-request", str(exc))
        except Exception as exc:
            # Do not leak local paths, payload data, or implementation tracebacks across the API boundary.
            return ServiceResponse.failure(request.request_id, "service.operation-failed", type(exc).__name__)

    @staticmethod
    def _require_empty_params(request: ServiceRequest) -> None:
        if request.params:
            raise ContractError("service method does not accept parameters")

    @staticmethod
    def _health_report(params: Mapping[str, Any]) -> HealthReport:
        expected = {"profile_id", "boot_target", "generated_at", "services"}
        if set(params) != expected:
            raise ContractError("health report parameters are incomplete")
        generated = params["generated_at"]
        try:
            generated_at = datetime.fromisoformat(str(generated).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ContractError("health report timestamp is invalid") from exc
        services = params["services"]
        if not isinstance(services, dict):
            raise ContractError("health report services must be an object")
        return HealthReport(str(params["profile_id"]), str(params["boot_target"]), generated_at, dict(services))
