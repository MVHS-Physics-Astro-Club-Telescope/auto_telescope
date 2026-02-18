import socket
import sys
from unittest.mock import MagicMock, patch

import pytest

from host.main import start_tcp_server, wait_for_pi, main


class TestStartTCPServer:
    def test_creates_listening_socket(self):
        server = start_tcp_server("127.0.0.1", 0)
        try:
            addr = server.getsockname()
            assert addr[0] == "127.0.0.1"
            assert addr[1] > 0
        finally:
            server.close()

    def test_accepts_connection(self):
        server = start_tcp_server("127.0.0.1", 0)
        port = server.getsockname()[1]
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(("127.0.0.1", port))
            peer, addr = server.accept()
            assert addr[0] == "127.0.0.1"
            peer.close()
            client.close()
        finally:
            server.close()


class TestWaitForPi:
    def test_returns_socket_on_connect(self):
        server = start_tcp_server("127.0.0.1", 0)
        port = server.getsockname()[1]
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(("127.0.0.1", port))
            result = wait_for_pi(server)
            assert result is not None
            result.close()
            client.close()
        finally:
            server.close()

    def test_returns_none_on_shutdown(self):
        import host.main as hm
        old = hm._shutdown
        hm._shutdown = True
        server = start_tcp_server("127.0.0.1", 0)
        try:
            result = wait_for_pi(server)
            assert result is None
        finally:
            server.close()
            hm._shutdown = old


class TestMainArgparse:
    def test_argparse_defaults(self):
        with patch.object(sys, "argv", ["host.main"]):
            with patch("host.main.run") as mock_run:
                main()
                mock_run.assert_called_once()
                args = mock_run.call_args
                assert args[0][1] == 5050  # default port

    def test_argparse_custom_port(self):
        with patch.object(sys, "argv", ["host.main", "--port", "9999"]):
            with patch("host.main.run") as mock_run:
                main()
                args = mock_run.call_args
                assert args[0][1] == 9999

    def test_argparse_simulate_flag(self):
        with patch.object(sys, "argv", ["host.main", "--simulate"]):
            with patch("host.main.run") as mock_run:
                main()
                mock_run.assert_called_once()
                call_args = mock_run.call_args
                # simulate is the 6th positional arg (index 5)
                assert call_args[0][5] is True
