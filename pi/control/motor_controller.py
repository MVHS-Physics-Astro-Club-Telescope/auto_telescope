import threading
from typing import Optional

from shared.commands.move_command import MoveCommand
from shared.commands.stop_command import StopCommand
from shared.enums.status_codes import StatusCode
from shared.errors.error_codes import ErrorCode
from pi.config.constants import (
    MAX_STEP_RATE_HZ,
    MIN_STEP_RATE_HZ,
    STEP_CHUNK_SIZE,
    STEPS_PER_DEGREE_ALT,
    STEPS_PER_DEGREE_AZ,
)
from pi.control.safety_manager import SafetyManager
from pi.hardware.motor_driver import MotorDriver, DIRECTION_FORWARD, DIRECTION_REVERSE
from pi.state.error_state import ErrorState
from pi.state.telescope_state import TelescopeStateManager
from pi.utils.logger import get_logger

logger = get_logger("motor_ctrl")


class MotorController:
    def __init__(
        self,
        alt_motor: MotorDriver,
        az_motor: MotorDriver,
        safety: SafetyManager,
        state_manager: TelescopeStateManager,
        error_state: ErrorState,
    ) -> None:
        self._alt_motor = alt_motor
        self._az_motor = az_motor
        self._safety = safety
        self._state = state_manager
        self._errors = error_state
        self.stop_event = threading.Event()

    def execute_move(self, cmd: MoveCommand) -> bool:
        if not self._safety.validate_move_target(cmd.target_alt_deg, cmd.target_az_deg):
            self._errors.add_error(
                ErrorCode.POSITION_OUT_OF_RANGE,
                f"Target alt={cmd.target_alt_deg} az={cmd.target_az_deg}",
            )
            return False

        self.stop_event.clear()
        self._state.set_status(StatusCode.MOVING)
        self._state.set_target(cmd.target_alt_deg, cmd.target_az_deg)

        rate_hz = self._speed_to_rate(cmd.speed)
        current_alt, current_az = self._state.get_position()

        alt_ok = self._move_axis(
            motor=self._alt_motor,
            current_deg=current_alt,
            target_deg=cmd.target_alt_deg,
            steps_per_deg=STEPS_PER_DEGREE_ALT,
            rate_hz=rate_hz,
            timeout_s=cmd.timeout_s,
            axis_name="alt",
        )

        if alt_ok and not self.stop_event.is_set():
            self._move_axis(
                motor=self._az_motor,
                current_deg=current_az,
                target_deg=cmd.target_az_deg,
                steps_per_deg=STEPS_PER_DEGREE_AZ,
                rate_hz=rate_hz,
                timeout_s=cmd.timeout_s,
                axis_name="az",
            )

        if self.stop_event.is_set():
            self._state.set_status(StatusCode.IDLE)
            return False

        self._state.update_position(cmd.target_alt_deg, cmd.target_az_deg)
        self._state.set_status(StatusCode.IDLE)
        self._state.set_target(None, None)
        return True

    def execute_stop(self, cmd: StopCommand) -> None:
        self.stop_event.set()
        self._alt_motor.stop()
        self._az_motor.stop()

        if cmd.emergency:
            self._safety.emergency_stop(
                cmd.reason if cmd.reason else "Emergency stop command"
            )
        else:
            self._state.set_status(StatusCode.IDLE)

    def _move_axis(
        self,
        motor: MotorDriver,
        current_deg: float,
        target_deg: float,
        steps_per_deg: float,
        rate_hz: float,
        timeout_s: float,
        axis_name: str,
    ) -> bool:
        delta_deg = target_deg - current_deg
        if abs(delta_deg) < 1e-6:
            return True

        direction = DIRECTION_FORWARD if delta_deg > 0 else DIRECTION_REVERSE
        total_steps = int(abs(delta_deg) * steps_per_deg)

        steps_done = 0
        while steps_done < total_steps:
            if self.stop_event.is_set():
                return False

            chunk = min(STEP_CHUNK_SIZE, total_steps - steps_done)
            actual = motor.step(
                direction=direction,
                num_steps=chunk,
                rate_hz=rate_hz,
                timeout_s=timeout_s,
                stop_event=self.stop_event,
            )
            steps_done += actual

            if actual < chunk:
                self._errors.add_error(
                    ErrorCode.MOTOR_TIMEOUT,
                    f"{axis_name} motor timeout at step {steps_done}/{total_steps}",
                )
                return False

        return True

    @staticmethod
    def _speed_to_rate(speed: float) -> float:
        speed = max(0.0, min(1.0, speed))
        return MIN_STEP_RATE_HZ + speed * (MAX_STEP_RATE_HZ - MIN_STEP_RATE_HZ)
