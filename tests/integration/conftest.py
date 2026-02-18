import queue
import socket
import threading
import time
from typing import Callable, Optional

import pytest

from host.comms.receiver import Receiver
from host.comms.sender import Sender
from host.state.session_logs import SessionLog
from host.state.telescope_state import HostTelescopeState
from pi.comms.message_parser import build_state_response
from pi.comms.tcp_client import TCPClient
from pi.control.focus_controller import FocusController
from pi.control.motor_controller import MotorController
from pi.control.safety_manager import SafetyManager
from pi.hardware.motor_driver import MockMotorDriver
from pi.hardware.sensor_reader import MockSensorReader
from pi.main import _dispatch_command
from pi.state.error_state import ErrorState
from pi.state.telescope_state import TelescopeStateManager
from shared.protocols.tcp_protocol import send_message


def wait_for_condition(
    predicate: Callable[[], bool],
    timeout: float = 2.0,
    poll: float = 0.02,
) -> bool:
    """Poll until predicate returns True or timeout expires."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(poll)
    return False


class StatusRecorder:
    """Monkey-patches TelescopeStateManager.set_status to record transitions."""

    def __init__(self, state_mgr: TelescopeStateManager) -> None:
        self._original = state_mgr.set_status
        self.history: list = []
        state_mgr.set_status = self._record  # type: ignore[assignment]

    def _record(self, status: str) -> None:
        self.history.append(status)
        self._original(status)


class IntegrationHarness:
    """Wires Host and Pi subsystems over real loopback TCP."""

    def __init__(self) -> None:
        # --- Host side ---
        self.host_state = HostTelescopeState()
        self.session_log = SessionLog()
        self.response_queue: queue.Queue[dict] = queue.Queue()
        self.sender = Sender(self.session_log, self.response_queue)
        self.receiver = Receiver(
            self.host_state, self.session_log, self.response_queue,
        )

        # --- Pi side ---
        self.alt_motor = MockMotorDriver()
        self.az_motor = MockMotorDriver()
        self.focus_motor = MockMotorDriver()
        self.sensor_reader = MockSensorReader()
        self.error_state = ErrorState()
        self.state_mgr = TelescopeStateManager(self.error_state)
        self.safety = SafetyManager(
            self.sensor_reader, self.state_mgr, self.error_state,
            [self.alt_motor, self.az_motor, self.focus_motor],
        )
        self.motor_ctrl = MotorController(
            self.alt_motor, self.az_motor, self.safety,
            self.state_mgr, self.error_state,
        )
        self.focus_ctrl = FocusController(
            self.focus_motor, self.safety,
            self.state_mgr, self.error_state,
        )

        # Status recorder — captures every set_status() call on the Pi side
        self.status_recorder = StatusRecorder(self.state_mgr)

        # --- TCP infrastructure ---
        self._server_sock: Optional[socket.socket] = None
        self._client_sock: Optional[socket.socket] = None
        self.tcp_client: Optional[TCPClient] = None
        self._msg_queue: queue.Queue[dict] = queue.Queue()
        self._pi_stop = threading.Event()
        self._pi_thread: Optional[threading.Thread] = None

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        # 1. TCP server on ephemeral port
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind(("127.0.0.1", 0))
        self._server_sock.listen(1)
        port = self._server_sock.getsockname()[1]

        # 2. Pi connects
        self.tcp_client = TCPClient("127.0.0.1", port, self.error_state)
        assert self.tcp_client.connect(), "Pi failed to connect"

        # 3. Host accepts
        self._client_sock, _ = self._server_sock.accept()
        self._client_sock.settimeout(1.0)

        # 4. Host wiring
        self.sender.set_socket(self._client_sock)
        self.receiver.start(self._client_sock)

        # 5. Pi receiver
        self.tcp_client.start_receiver(self._msg_queue)

        # 6. Pi dispatch thread
        self._pi_stop.clear()
        self._pi_thread = threading.Thread(
            target=self._pi_dispatch_loop,
            name="pi-dispatch-test",
            daemon=True,
        )
        self._pi_thread.start()

    def stop(self) -> None:
        # 1. Signal Pi dispatch loop
        self._pi_stop.set()

        # 2. Stop Host receiver
        self.receiver.stop()

        # 3. Disconnect Pi
        if self.tcp_client is not None:
            self.tcp_client.disconnect()

        # 4. Join Pi dispatch thread
        if self._pi_thread is not None and self._pi_thread.is_alive():
            self._pi_thread.join(timeout=2.0)

        # 5. Close sockets
        for sock in (self._client_sock, self._server_sock):
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass

    # -- helpers ------------------------------------------------------------

    def send_state_report(self) -> None:
        """Manually trigger a Pi -> Host state report."""
        snapshot = self.state_mgr.get_snapshot()
        self.tcp_client.send(build_state_response(snapshot))

    def send_raw(self, data: dict) -> None:
        """Send raw data from Host to Pi, bypassing Sender validation."""
        send_message(self._client_sock, data)

    # -- internal -----------------------------------------------------------

    def _pi_dispatch_loop(self) -> None:
        while not self._pi_stop.is_set():
            try:
                data = self._msg_queue.get(timeout=0.05)
            except queue.Empty:
                continue
            try:
                _dispatch_command(
                    data, self.tcp_client, self.motor_ctrl,
                    self.focus_ctrl, self.state_mgr,
                )
            except Exception:
                pass  # keep dispatch loop alive


@pytest.fixture
def harness():
    h = IntegrationHarness()
    h.start()
    yield h
    h.stop()
