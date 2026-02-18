import queue
import socket
import struct
import json
import threading
import time

import pytest

from shared.enums.status_codes import StatusCode
from shared.state.telescope_state import TelescopeState
from host.comms.receiver import Receiver
from host.state.session_logs import SessionLog
from host.state.telescope_state import HostTelescopeState


def _make_socket_pair():
    """Create a connected pair of sockets for testing."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", port))
    peer, _ = server.accept()
    server.close()
    return client, peer


def _send_raw(sock, data):
    """Send a framed message."""
    payload = json.dumps(data).encode("utf-8")
    header = struct.pack("!I", len(payload))
    sock.sendall(header + payload)


@pytest.fixture
def setup():
    ts = HostTelescopeState()
    sl = SessionLog()
    rq = queue.Queue()
    client, peer = _make_socket_pair()
    client.settimeout(1.0)
    receiver = Receiver(ts, sl, rq)
    yield ts, sl, rq, client, peer, receiver
    receiver.stop()
    client.close()
    peer.close()


class TestReceiver:
    def test_state_report_updates_telescope_state(self, setup):
        ts, sl, rq, client, peer, receiver = setup
        receiver.start(client)

        state_data = TelescopeState(
            current_alt_deg=45.0,
            current_az_deg=90.0,
            status=StatusCode.IDLE,
        ).to_dict()
        state_data["message_type"] = "state_report"
        _send_raw(peer, state_data)

        time.sleep(0.2)
        assert ts.has_state()
        pos = ts.get_position()
        assert pos[0] == pytest.approx(45.0)

    def test_ack_goes_to_response_queue(self, setup):
        ts, sl, rq, client, peer, receiver = setup
        receiver.start(client)

        _send_raw(peer, {"message_type": "ack", "command_id": "abc123"})
        time.sleep(0.2)
        msg = rq.get(timeout=1.0)
        assert msg["command_id"] == "abc123"

    def test_error_goes_to_response_queue(self, setup):
        ts, sl, rq, client, peer, receiver = setup
        receiver.start(client)

        _send_raw(peer, {"message_type": "error", "command_id": "x", "error": "bad"})
        time.sleep(0.2)
        msg = rq.get(timeout=1.0)
        assert msg["message_type"] == "error"

    def test_disconnect_stops_receiver(self, setup):
        ts, sl, rq, client, peer, receiver = setup
        receiver.start(client)
        time.sleep(0.1)

        peer.close()
        time.sleep(0.5)
        assert not receiver.is_alive()

    def test_stop_stops_cleanly(self, setup):
        ts, sl, rq, client, peer, receiver = setup
        receiver.start(client)
        assert receiver.is_alive()
        receiver.stop()
        assert not receiver.is_alive()

    def test_bad_state_report_logged(self, setup):
        ts, sl, rq, client, peer, receiver = setup
        receiver.start(client)

        _send_raw(peer, {"message_type": "state_report", "bad": "data"})
        time.sleep(0.2)
        assert not ts.has_state()

    def test_unknown_message_type_ignored(self, setup):
        ts, sl, rq, client, peer, receiver = setup
        receiver.start(client)

        _send_raw(peer, {"message_type": "weird", "data": 123})
        time.sleep(0.2)
        assert rq.empty()

    def test_multiple_state_reports(self, setup):
        ts, sl, rq, client, peer, receiver = setup
        receiver.start(client)

        for i in range(3):
            state_data = TelescopeState(
                current_alt_deg=float(i * 10),
                current_az_deg=float(i * 20),
                status=StatusCode.IDLE,
            ).to_dict()
            state_data["message_type"] = "state_report"
            _send_raw(peer, state_data)

        time.sleep(0.3)
        pos = ts.get_position()
        assert pos[0] == pytest.approx(20.0)
        assert pos[1] == pytest.approx(40.0)
