import queue
import socket
import threading
from typing import Optional

from shared.protocols.tcp_protocol import ProtocolError, recv_message
from shared.state.telescope_state import TelescopeState
from host.state.telescope_state import HostTelescopeState
from host.state.session_logs import SessionLog
from host.utils.logger import get_logger, log_state_received

logger = get_logger("receiver")


class Receiver:
    """Receives messages from Pi and dispatches them."""

    def __init__(
        self,
        telescope_state: HostTelescopeState,
        session_log: SessionLog,
        response_queue: "queue.Queue[dict]",
    ) -> None:
        self._telescope_state = telescope_state
        self._session_log = session_log
        self._response_queue = response_queue
        self._shutdown = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._sock: Optional[socket.socket] = None

    def start(self, client_sock: socket.socket) -> None:
        self._sock = client_sock
        self._shutdown.clear()
        self._thread = threading.Thread(
            target=self._receive_loop,
            name="host-receiver",
            daemon=True,
        )
        self._thread.start()
        logger.info("Receiver started")

    def stop(self) -> None:
        self._shutdown.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Receiver stopped")

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _receive_loop(self) -> None:
        while not self._shutdown.is_set():
            try:
                msg = recv_message(self._sock)
            except socket.timeout:
                continue
            except (ProtocolError, OSError) as e:
                if not self._shutdown.is_set():
                    logger.error("Receive error: %s", e)
                    self._session_log.log_error("Receive error: %s" % e)
                break

            if msg is None:
                logger.warning("Pi disconnected")
                self._session_log.log_error("Pi disconnected")
                break

            self._dispatch(msg)

    def _dispatch(self, msg: dict) -> None:
        msg_type = msg.get("message_type")

        if msg_type == "state_report":
            try:
                state = TelescopeState.from_dict(msg)
                self._telescope_state.update_from_pi(state)
                self._session_log.log_state(msg)
                log_state_received(logger, msg)
            except (KeyError, TypeError, ValueError) as e:
                logger.error("Bad state report: %s", e)
                self._session_log.log_error("Bad state report: %s" % e)

        elif msg_type in ("ack", "error"):
            self._response_queue.put(msg)
            if msg_type == "error":
                logger.warning(
                    "Error from Pi: %s (cmd=%s)",
                    msg.get("error", "?"),
                    msg.get("command_id", "?"),
                )
        else:
            logger.warning("Unknown message type: %s", msg_type)
