import queue
import socket
import threading
import time
from typing import Optional

from shared.commands.move_command import MoveCommand
from shared.commands.focus_command import FocusCommand, FOCUS_IN, FOCUS_OUT
from shared.commands.stop_command import StopCommand
from shared.enums.command_types import CommandType
from shared.protocols.tcp_protocol import ProtocolError, send_message
from host.comms.validator import validate_outgoing_command
from host.config.constants import COMMAND_ACK_TIMEOUT_S
from host.state.session_logs import SessionLog
from host.utils.logger import get_logger, log_command_sent

logger = get_logger("sender")


class Sender:
    """Sends commands to Pi over TCP."""

    def __init__(
        self,
        session_log: SessionLog,
        response_queue: "queue.Queue[dict]",
    ) -> None:
        self._session_log = session_log
        self._response_queue = response_queue
        self._sock: Optional[socket.socket] = None
        self._lock = threading.Lock()

    def set_socket(self, sock: socket.socket) -> None:
        with self._lock:
            self._sock = sock

    def send_move(
        self, alt: float, az: float, speed: float = 0.5
    ) -> Optional[str]:
        cmd = MoveCommand(target_alt_deg=alt, target_az_deg=az, speed=speed)
        return self._send_command(cmd.to_dict(), cmd.command_id)

    def send_focus(self, direction: str, steps: int) -> Optional[str]:
        cmd = FocusCommand(direction=direction, steps=steps)
        return self._send_command(cmd.to_dict(), cmd.command_id)

    def send_stop(self, emergency: bool = False) -> Optional[str]:
        cmd = StopCommand(emergency=emergency)
        return self._send_command(cmd.to_dict(), cmd.command_id)

    def send_status_request(self) -> bool:
        data = {
            "command_type": CommandType.STATUS_REQUEST,
            "timestamp": time.time(),
        }
        with self._lock:
            if self._sock is None:
                return False
            try:
                send_message(self._sock, data)
                return True
            except (ProtocolError, OSError) as e:
                logger.error("Status request send failed: %s", e)
                return False

    def wait_for_ack(
        self, command_id: str, timeout: Optional[float] = None
    ) -> Optional[dict]:
        if timeout is None:
            timeout = COMMAND_ACK_TIMEOUT_S
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                msg = self._response_queue.get(timeout=min(remaining, 0.5))
            except queue.Empty:
                continue
            if msg.get("command_id") == command_id:
                return msg
            # Put back if not ours (unlikely but safe)
            self._response_queue.put(msg)
        logger.warning("Ack timeout for command %s", command_id)
        return None

    def _send_command(self, data: dict, command_id: str) -> Optional[str]:
        errors = validate_outgoing_command(data)
        if errors:
            logger.error("Validation failed: %s", errors)
            self._session_log.log_error(
                "Validation failed", {"errors": errors}
            )
            return None

        with self._lock:
            if self._sock is None:
                logger.error("No socket, cannot send")
                return None
            try:
                send_message(self._sock, data)
            except (ProtocolError, OSError) as e:
                logger.error("Send failed: %s", e)
                self._session_log.log_error("Send failed: %s" % e)
                return None

        log_command_sent(
            logger,
            data.get("command_type", "unknown"),
            {"id": command_id},
        )
        self._session_log.log_command(
            data.get("command_type", "unknown"),
            {"command_id": command_id},
        )
        return command_id
