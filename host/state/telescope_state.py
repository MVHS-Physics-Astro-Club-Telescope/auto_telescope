import threading
import time
from typing import Dict, Optional

from shared.enums.status_codes import StatusCode
from shared.state.telescope_state import TelescopeState
from host.utils.logger import get_logger

logger = get_logger("telescope_state")


class HostTelescopeState:
    """Thread-safe store of the latest telescope state received from Pi."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state: Optional[TelescopeState] = None
        self._last_update: float = 0.0
        self._tracking_target: Optional[str] = None

    def update_from_pi(self, state: TelescopeState) -> None:
        with self._lock:
            self._state = state
            self._last_update = time.monotonic()
        logger.debug(
            "State updated: alt=%.2f az=%.2f status=%s",
            state.current_alt_deg,
            state.current_az_deg,
            state.status,
        )

    def get_latest(self) -> Optional[TelescopeState]:
        with self._lock:
            return self._state

    def get_position(self) -> Optional[tuple]:
        with self._lock:
            if self._state is None:
                return None
            return (self._state.current_alt_deg, self._state.current_az_deg)

    def get_status(self) -> str:
        with self._lock:
            if self._state is None:
                return StatusCode.IDLE
            return self._state.status

    def seconds_since_update(self) -> float:
        with self._lock:
            if self._last_update == 0.0:
                return float("inf")
            return time.monotonic() - self._last_update

    def set_tracking_target(self, name: str) -> None:
        with self._lock:
            self._tracking_target = name
        logger.info("Tracking target set: %s", name)

    def clear_tracking_target(self) -> None:
        with self._lock:
            self._tracking_target = None
        logger.info("Tracking target cleared")

    def get_tracking_target(self) -> Optional[str]:
        with self._lock:
            return self._tracking_target

    def has_state(self) -> bool:
        with self._lock:
            return self._state is not None
