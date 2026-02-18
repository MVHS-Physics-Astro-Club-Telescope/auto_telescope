from typing import List

from shared.enums.status_codes import StatusCode
from shared.errors.error_codes import ErrorCode
from pi.config.constants import (
    ALT_MAX_DEG,
    ALT_MIN_DEG,
    AZ_MAX_DEG,
    AZ_MIN_DEG,
    WATCHDOG_TIMEOUT_S,
)
from pi.hardware.motor_driver import MotorDriver
from pi.hardware.sensor_reader import SensorReader
from pi.state.error_state import ErrorState
from pi.state.telescope_state import TelescopeStateManager
from pi.utils.logger import get_logger
from pi.utils.timer import Timeout

logger = get_logger("safety")


class SafetyManager:
    def __init__(
        self,
        sensor_reader: SensorReader,
        state_manager: TelescopeStateManager,
        error_state: ErrorState,
        motors: List[MotorDriver],
    ) -> None:
        self._sensors = sensor_reader
        self._state = state_manager
        self._errors = error_state
        self._motors = motors
        self._watchdog = Timeout(WATCHDOG_TIMEOUT_S)

    def check(self) -> bool:
        safe = True

        if not self._check_limit_switches():
            safe = False

        if not self._check_position_bounds():
            safe = False

        if not self._check_watchdog():
            safe = False

        return safe

    def validate_move_target(self, alt_deg: float, az_deg: float) -> bool:
        if alt_deg < ALT_MIN_DEG or alt_deg > ALT_MAX_DEG:
            logger.warning(
                "Move target alt=%.2f outside bounds [%.1f, %.1f]",
                alt_deg, ALT_MIN_DEG, ALT_MAX_DEG,
            )
            return False
        if az_deg < AZ_MIN_DEG or az_deg > AZ_MAX_DEG:
            logger.warning(
                "Move target az=%.2f outside bounds [%.1f, %.1f]",
                az_deg, AZ_MIN_DEG, AZ_MAX_DEG,
            )
            return False
        return True

    def emergency_stop(self, reason: str) -> None:
        logger.error("EMERGENCY STOP: %s", reason)
        for motor in self._motors:
            motor.stop()
            motor.disable()
        self._errors.add_error(ErrorCode.SAFETY_EMERGENCY_STOP, reason)
        self._state.set_status(StatusCode.EMERGENCY_STOP)

    def feed_watchdog(self) -> None:
        self._watchdog.reset()

    def _check_watchdog(self) -> bool:
        if self._watchdog.is_expired():
            self._errors.add_error(
                ErrorCode.SAFETY_WATCHDOG_TIMEOUT, "Watchdog timeout"
            )
            self.emergency_stop("Watchdog timeout")
            return False
        self._errors.clear_error(ErrorCode.SAFETY_WATCHDOG_TIMEOUT)
        return True

    def _check_limit_switches(self) -> bool:
        limits = self._sensors.read_limit_switches()
        if limits.any_hit:
            self._errors.add_error(
                ErrorCode.POSITION_LIMIT_HIT, "Limit switch triggered"
            )
            self.emergency_stop("Limit switch triggered")
            return False
        self._errors.clear_error(ErrorCode.POSITION_LIMIT_HIT)
        return True

    def _check_position_bounds(self) -> bool:
        alt, az = self._state.get_position()
        if alt < ALT_MIN_DEG or alt > ALT_MAX_DEG:
            self._errors.add_error(
                ErrorCode.SAFETY_LIMIT_EXCEEDED,
                f"Alt {alt:.2f} outside bounds",
            )
            return False
        if az < AZ_MIN_DEG or az > AZ_MAX_DEG:
            self._errors.add_error(
                ErrorCode.SAFETY_LIMIT_EXCEEDED,
                f"Az {az:.2f} outside bounds",
            )
            return False
        self._errors.clear_error(ErrorCode.SAFETY_LIMIT_EXCEEDED)
        return True
