import json
import socket
import struct
import threading
import time

import pytest

from shared.protocols.constants import HEADER_SIZE
from pi.comms.tcp_client import TCPClient
from pi.state.error_state import ErrorState
from shared.errors.error_codes import ErrorCode


def _make_server():
    """Create a test TCP server that accepts one connection."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    return server, port


def _encode_msg(data: dict) -> bytes:
    payload = json.dumps(data).encode("utf-8")
    return struct.pack("!I", len(payload)) + payload


class TestTCPClientConnect:
    def test_connect_success(self):
        server, port = _make_server()
        try:
            es = ErrorState()
            client = TCPClient("127.0.0.1", port, es)
            assert client.connect() is True
            assert client.is_connected()
        finally:
            client.disconnect()
            server.close()

    def test_connect_failure(self):
        es = ErrorState()
        client = TCPClient("127.0.0.1", 1, es)
        assert client.connect() is False
        assert not client.is_connected()
        assert ErrorCode.COMMS_DISCONNECT in es.get_active_codes()

    def test_disconnect(self):
        server, port = _make_server()
        try:
            es = ErrorState()
            client = TCPClient("127.0.0.1", port, es)
            client.connect()
            client.disconnect()
            assert not client.is_connected()
        finally:
            server.close()


class TestTCPClientSendRecv:
    def test_send_data(self):
        server, port = _make_server()
        try:
            es = ErrorState()
            client = TCPClient("127.0.0.1", port, es)
            client.connect()
            conn, _ = server.accept()

            msg = {"command_type": "status_request"}
            assert client.send(msg) is True

            # Read what the server received
            header = conn.recv(HEADER_SIZE)
            length = struct.unpack("!I", header)[0]
            payload = conn.recv(length)
            received = json.loads(payload)
            assert received["command_type"] == "status_request"

            conn.close()
        finally:
            client.disconnect()
            server.close()

    def test_receive_data(self):
        server, port = _make_server()
        try:
            es = ErrorState()
            client = TCPClient("127.0.0.1", port, es)
            client.connect()
            conn, _ = server.accept()

            msg = {"message_type": "state_report", "status": "idle"}
            conn.sendall(_encode_msg(msg))

            received = client.receive()
            assert received is not None
            assert received["message_type"] == "state_report"

            conn.close()
        finally:
            client.disconnect()
            server.close()

    def test_receive_timeout_returns_none(self):
        server, port = _make_server()
        try:
            es = ErrorState()
            client = TCPClient("127.0.0.1", port, es)
            client.connect()
            conn, _ = server.accept()

            # Set a very short timeout so we don't wait long
            client._sock.settimeout(0.1)
            result = client.receive()
            assert result is None

            conn.close()
        finally:
            client.disconnect()
            server.close()

    def test_send_when_disconnected(self):
        es = ErrorState()
        client = TCPClient("127.0.0.1", 1, es)
        assert client.send({"test": True}) is False
