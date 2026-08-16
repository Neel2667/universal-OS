"""Linux Unix-domain-socket transport for the local UniversalOS service protocol.

This is a host-side transport reference that authenticates the connecting peer
with Linux SO_PEERCRED before dispatching a bounded newline-delimited JSON
request. It has no TCP listener, no network code, no bearer-token parser, and
no hardware/bootloader access.
"""

from __future__ import annotations

import json
import os
import socket
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .protocol import CallerContext, LocalServiceGateway, ServiceRequest, ServiceResponse

MAX_FRAME_BYTES = 64 * 1024


@dataclass(frozen=True)
class LinuxPeerCredentials:
    pid: int
    uid: int
    gid: int


class PeerCredentialPolicy:
    """Maps platform-authenticated local Unix UIDs to fixed service contexts.

    A production image should generate this mapping from service-manager and
    mandatory-access-control policy, not from application-provided data.
    """

    def __init__(self, contexts_by_uid: Mapping[int, CallerContext]) -> None:
        self._contexts_by_uid = dict(contexts_by_uid)

    def authenticate(self, credentials: LinuxPeerCredentials) -> CallerContext | None:
        return self._contexts_by_uid.get(credentials.uid)


class UnixServiceServer:
    """One-request-at-a-time reference server for local Unix-domain IPC."""

    def __init__(self, path: Path, gateway: LocalServiceGateway, policy: PeerCredentialPolicy) -> None:
        self.path = path
        self.gateway = gateway
        self.policy = policy
        self._socket: socket.socket | None = None

    def start(self) -> None:
        if self._socket is not None:
            raise RuntimeError("Unix service server is already started")
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.path.exists() or self.path.is_symlink():
            raise RuntimeError("refusing to replace an existing Unix service socket path")
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            server.bind(str(self.path))
            os.chmod(self.path, 0o660)
            server.listen(8)
        except Exception:
            server.close()
            self.path.unlink(missing_ok=True)
            raise
        self._socket = server

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None
        self.path.unlink(missing_ok=True)

    def serve_once(self) -> None:
        if self._socket is None:
            raise RuntimeError("Unix service server has not been started")
        connection, _ = self._socket.accept()
        with connection:
            response = self._handle(connection)
            connection.sendall(json.dumps(response.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n")

    def _handle(self, connection: socket.socket) -> ServiceResponse:
        credentials = self._peer_credentials(connection)
        caller = self.policy.authenticate(credentials)
        if caller is None:
            return ServiceResponse.failure("unknown", "service.permission-denied", "local peer is not an authorized service principal")
        raw = self._read_frame(connection)
        if raw is None:
            return ServiceResponse.failure("unknown", "service.invalid-request", "request frame is invalid")
        try:
            request_raw = json.loads(raw.decode("utf-8"))
            if not isinstance(request_raw, dict):
                raise ValueError("request is not an object")
            request = ServiceRequest.from_dict(request_raw)
        except Exception:
            return ServiceResponse.failure("unknown", "service.invalid-request", "request envelope is invalid")
        return self.gateway.dispatch(caller, request)

    @staticmethod
    def _peer_credentials(connection: socket.socket) -> LinuxPeerCredentials:
        if not hasattr(socket, "SO_PEERCRED"):
            raise RuntimeError("SO_PEERCRED is required for this Linux local IPC reference")
        raw = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
        pid, uid, gid = struct.unpack("3i", raw)
        return LinuxPeerCredentials(pid, uid, gid)

    @staticmethod
    def _read_frame(connection: socket.socket) -> bytes | None:
        payload = bytearray()
        while len(payload) <= MAX_FRAME_BYTES:
            chunk = connection.recv(min(4096, MAX_FRAME_BYTES + 1 - len(payload)))
            if not chunk:
                break
            payload.extend(chunk)
            if b"\n" in chunk:
                break
        if len(payload) > MAX_FRAME_BYTES or not payload.endswith(b"\n"):
            return None
        return bytes(payload[:-1])
