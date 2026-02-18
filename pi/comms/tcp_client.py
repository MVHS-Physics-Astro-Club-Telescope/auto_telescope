import queue
import socket
import threading
import time
from typing import Callable, Optional

from shared.protocols.constants import CONNECT_TIMEOUT_S, RECV_TIMEOUT_S
from shared.protocols.tcp_protocol import (
    ProtocolError,
    recv_message,
    send_message,
)
from pi.config.constants import MAX_RECONNECT_ATTEMPTS, RECONNECT_DELAY_S
from pi.state.error_state import ErrorState
from shared.errors.error_codes import ErrorCode
from pi.utils.logger import get_logger

logger = get_logger("tcp_client")


class TCPClient:
    def __init__(self, host: str, port: int, error_state: ErrorState) -> None:
        self._host = host
        self._port = port
        self._errors = error_state
        self._sock: Optional[socket.socket] = None
        self._connected = False
        self._receiver_thread: Optional[threading.Thread] = None
        self._shutdown = threading.Event()
        self._lock = threading.Lock()

    def connect(self) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(CONNECT_TIMEOUT_S)
            sock.connect((self._host, self._port))
            sock.settimeout(RECV_TIMEOUT_S)
            with self._lock:
                self._sock = sock
                self._connected = True
            self._errors.clear_error(ErrorCode.COMMS_DISCONNECT)
            logger.info("Connected to %s:%d", self._host, self._port)
            return True
        except (socket.error, OSError) as e:
            logger.error("Connect failed: %s", e)
            self._errors.add_error(ErrorCode.COMMS_DISCONNECT, str(e))
            return False

    def disconnect(self) -> None:
        self._shutdown.set()
        with self._lock:
            self._connected = False
            if self._sock is not None:
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None
        if self._receiver_thread is not None and self._receiver_thread.is_alive():
            self._receiver_thread.join(timeout=2.0)
        logger.info("Disconnected")

    def is_connected(self) -> bool:
        with self._lock:
            return self._connected

    def send(self, data: dict) -> bool:
        with self._lock:
            if not self._connected or self._sock is None:
                return False
            try:
                send_message(self._sock, data)
                return True
            except (ProtocolError, OSError) as e:
                logger.error("Send failed: %s", e)
                self._connected = False
                self._errors.add_error(ErrorCode.COMMS_DISCONNECT, str(e))
                return False

    def receive(self) -> Optional[dict]:
        with self._lock:
            if not self._connected or self._sock is None:
                return None
            sock = self._sock

        try:
            return recv_message(sock)
        except socket.timeout:
            return None
        except (ProtocolError, OSError) as e:
            logger.error("Receive failed: %s", e)
            with self._lock:
                self._connected = False
            self._errors.add_error(ErrorCode.COMMS_DISCONNECT, str(e))
            return None

    def start_receiver(self, msg_queue: "queue.Queue[dict]") -> None:
        self._shutdown.clear()
        self._receiver_thread = threading.Thread(
            target=self._receiver_loop,
            args=(msg_queue,),
            daemon=True,
        )
        self._receiver_thread.start()

    def reconnect(self) -> bool:
        for attempt in range(1, MAX_RECONNECT_ATTEMPTS + 1):
            if self._shutdown.is_set():
                return False
            logger.info("Reconnect attempt %d/%d", attempt, MAX_RECONNECT_ATTEMPTS)
            with self._lock:
                if self._sock is not None:
                    try:
                        self._sock.close()
                    except OSError:
                        pass
                    self._sock = None
                self._connected = False
            if self.connect():
                return True
            time.sleep(RECONNECT_DELAY_S)
        logger.error("Reconnect failed after %d attempts", MAX_RECONNECT_ATTEMPTS)
        return False

    def _receiver_loop(self, msg_queue: "queue.Queue[dict]") -> None:
        while not self._shutdown.is_set():
            msg = self.receive()
            if msg is not None:
                msg_queue.put(msg)
            elif not self.is_connected():
                if not self.reconnect():
                    break
