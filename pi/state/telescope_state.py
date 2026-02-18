import threading
from typing import Optional

from shared.enums.status_codes import StatusCode
from shared.state.telescope_state import TelescopeState
from pi.state.error_state import ErrorState
from pi.utils.logger import get_logger

logger = get_logger("telescope_state")


class TelescopeStateManager:
    def __init__(self, error_state: ErrorState) -> None:
        self._lock = threading.Lock()
        self._error_state = error_state
        self._current_alt = 0.0
        self._current_az = 0.0
        self._target_alt: Optional[float] = None
        self._target_az: Optional[float] = None
        self._status = StatusCode.IDLE
        self._focus_position: Optional[int] = None
        self._is_tracking = False

    def update_position(self, alt_deg: float, az_deg: float) -> None:
        with self._lock:
            self._current_alt = alt_deg
            self._current_az = az_deg

    def set_target(
        self, alt_deg: Optional[float], az_deg: Optional[float]
    ) -> None:
        with self._lock:
            self._target_alt = alt_deg
            self._target_az = az_deg

    def set_status(self, status: str) -> None:
        with self._lock:
            self._status = status

    def set_focus_position(self, position: Optional[int]) -> None:
        with self._lock:
            self._focus_position = position

    def set_tracking(self, tracking: bool) -> None:
        with self._lock:
            self._is_tracking = tracking

    def get_position(self) -> tuple:
        with self._lock:
            return (self._current_alt, self._current_az)

    def get_status(self) -> str:
        with self._lock:
            return self._status

    def get_snapshot(self) -> TelescopeState:
        with self._lock:
            return TelescopeState(
                current_alt_deg=self._current_alt,
                current_az_deg=self._current_az,
                status=self._status,
                target_alt_deg=self._target_alt,
                target_az_deg=self._target_az,
                error_codes=self._error_state.get_active_codes(),
                focus_position=self._focus_position,
                is_tracking=self._is_tracking,
            )
