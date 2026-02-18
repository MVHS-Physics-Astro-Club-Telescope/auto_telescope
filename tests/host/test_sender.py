import json
import queue
import socket
import struct
import threading
import time

import pytest

from host.comms.sender import Sender
from host.state.session_logs import SessionLog


def _make_socket_pair():
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


def _recv_raw(sock):
    """Receive a framed message."""
    sock.settimeout(2.0)
    header = b""
    while len(header) < 4:
        chunk = sock.recv(4 - len(header))
        if not chunk:
            return None
        header += chunk
    length = struct.unpack("!I", header)[0]
    payload = b""
    while len(payload) < length:
        chunk = sock.recv(length - len(payload))
        if not chunk:
            return None
        payload += chunk
    return json.loads(payload.decode("utf-8"))


@pytest.fixture
def setup():
    sl = SessionLog()
    rq = queue.Queue()
    sender = Sender(sl, rq)
    client, peer = _make_socket_pair()
    sender.set_socket(client)
    yield sender, sl, rq, client, peer
    client.close()
    peer.close()


class TestSender:
    def test_send_move(self, setup):
        sender, sl, rq, client, peer = setup
        cmd_id = sender.send_move(45.0, 90.0, 0.5)
        assert cmd_id is not None
        msg = _recv_raw(peer)
        assert msg["command_type"] == "move"
        assert msg["target_alt_deg"] == 45.0

    def test_send_focus(self, setup):
        sender, sl, rq, client, peer = setup
        cmd_id = sender.send_focus("in", 100)
        assert cmd_id is not None
        msg = _recv_raw(peer)
        assert msg["command_type"] == "focus"
        assert msg["direction"] == "in"
        assert msg["steps"] == 100

    def test_send_stop(self, setup):
        sender, sl, rq, client, peer = setup
        cmd_id = sender.send_stop(emergency=True)
        assert cmd_id is not None
        msg = _recv_raw(peer)
        assert msg["command_type"] == "stop"
        assert msg["emergency"] is True

    def test_send_status_request(self, setup):
        sender, sl, rq, client, peer = setup
        ok = sender.send_status_request()
        assert ok is True
        msg = _recv_raw(peer)
        assert msg["command_type"] == "status_request"

    def test_send_without_socket_fails(self):
        sl = SessionLog()
        rq = queue.Queue()
        sender = Sender(sl, rq)
        cmd_id = sender.send_move(10.0, 20.0)
        assert cmd_id is None

    def test_send_invalid_command_rejected(self, setup):
        sender, sl, rq, client, peer = setup
        # Altitude out of range
        cmd_id = sender.send_move(200.0, 90.0)
        assert cmd_id is None

    def test_session_log_records_command(self, setup):
        sender, sl, rq, client, peer = setup
        sender.send_move(45.0, 90.0)
        entries = sl.get_by_category("command")
        assert len(entries) == 1

    def test_wait_for_ack_success(self, setup):
        sender, sl, rq, client, peer = setup
        cmd_id = sender.send_move(45.0, 90.0)
        rq.put({"message_type": "ack", "command_id": cmd_id})
        result = sender.wait_for_ack(cmd_id, timeout=1.0)
        assert result is not None
        assert result["command_id"] == cmd_id

    def test_wait_for_ack_timeout(self, setup):
        sender, sl, rq, client, peer = setup
        result = sender.wait_for_ack("nonexistent", timeout=0.2)
        assert result is None

    def test_send_stop_non_emergency(self, setup):
        sender, sl, rq, client, peer = setup
        cmd_id = sender.send_stop(emergency=False)
        assert cmd_id is not None
        msg = _recv_raw(peer)
        assert msg["emergency"] is False
