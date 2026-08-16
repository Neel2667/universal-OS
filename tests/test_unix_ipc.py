from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from universal_core.contracts import HardwareProfile
from universal_core.health import HealthPolicy
from universal_core.protocol import CallerContext, LocalServiceGateway
from universal_core.services import UniversalSystemServices
from universal_core.unix_ipc import PeerCredentialPolicy, UnixServiceServer


def profile() -> HardwareProfile:
    return HardwareProfile.from_dict(json.loads((ROOT / "testdata/profiles/synthetic-orion-arm64.json").read_text(encoding="utf-8")))


class UnixIpcTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        services = UniversalSystemServices(
            profile(),
            active_target="a",
            journal_directory=root / "journal",
            staging_directory=root / "staging",
            health_policy=HealthPolicy(frozenset({"system-manager"})),
        )
        self.path = root / "run" / "universalos.sock"
        self.server = UnixServiceServer(
            self.path,
            LocalServiceGateway(services),
            PeerCredentialPolicy({os.getuid(): CallerContext("test-ui", frozenset({"uos.device.read"}))}),
        )
        self.server.start()

    def tearDown(self) -> None:
        self.server.close()
        self.temp.cleanup()

    def round_trip(self, payload: bytes) -> dict:
        worker = threading.Thread(target=self.server.serve_once, daemon=True)
        worker.start()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(str(self.path))
            client.sendall(payload)
            response = b""
            while not response.endswith(b"\n"):
                chunk = client.recv(4096)
                if not chunk:
                    break
                response += chunk
        worker.join(timeout=2)
        self.assertFalse(worker.is_alive())
        return json.loads(response)

    def test_socket_mode_and_peer_authenticated_status_request(self) -> None:
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o660)
        response = self.round_trip(b'{"schema_version":1,"request_id":"status-1","service":"device","method":"get-status","params":{}}\n')
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"]["profile_id"], "uos.profile.synthetic.orion-arm64-v1")

    def test_peer_capability_blocks_update_operation(self) -> None:
        response = self.round_trip(b'{"schema_version":1,"request_id":"update-1","service":"update","method":"get-status","params":{}}\n')
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "service.permission-denied")

    def test_invalid_wire_payload_returns_bounded_error(self) -> None:
        response = self.round_trip(b'{not-json}\n')
        self.assertFalse(response["ok"])
        self.assertEqual(response["request_id"], "unknown")
        self.assertEqual(response["error"]["code"], "service.invalid-request")
        self.assertNotIn(str(self.path.parent), json.dumps(response))


if __name__ == "__main__":
    unittest.main()
