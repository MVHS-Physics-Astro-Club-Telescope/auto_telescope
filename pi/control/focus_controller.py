from shared.commands.focus_command import FocusCommand, FOCUS_IN, FOCUS_OUT
from shared.enums.status_codes import StatusCode
from shared.errors.error_codes import ErrorCode
from pi.config.constants import FOCUS_POSITION_MAX, FOCUS_POSITION_MIN, MIN_STEP_RATE_HZ
from pi.control.safety_manager import SafetyManager
from pi.hardware.motor_driver import MotorDriver, DIRECTION_FORWARD, DIRECTION_REVERSE
from pi.state.error_state import ErrorState
from pi.state.telescope_state import TelescopeStateManager
from pi.utils.logger import get_logger

logger = get_logger("focus_ctrl")


class FocusController:
    def __init__(
        self,
        focus_motor: MotorDriver,
        safety: SafetyManager,
        state_manager: TelescopeStateManager,
        error_state: ErrorState,
    ) -> None:
        self._motor = focus_motor
        self._safety = safety
        self._state = state_manager
        self._errors = error_state
        self._position = 0

    def execute_focus(self, cmd: FocusCommand) -> bool:
        direction = DIRECTION_FORWARD if cmd.direction == FOCUS_IN else DIRECTION_REVERSE
        new_position = self._position + (
            cmd.steps if cmd.direction == FOCUS_IN else -cmd.steps
        )

        if new_position < FOCUS_POSITION_MIN:
            self._errors.add_error(
                ErrorCode.FOCUS_LIMIT_HIT,
                f"Focus would go below min ({new_position} < {FOCUS_POSITION_MIN})",
            )
            return False

        if new_position > FOCUS_POSITION_MAX:
            self._errors.add_error(
                ErrorCode.FOCUS_LIMIT_HIT,
                f"Focus would exceed max ({new_position} > {FOCUS_POSITION_MAX})",
            )
            return False

        self._state.set_status(StatusCode.FOCUSING)

        actual = self._motor.step(
            direction=direction,
            num_steps=cmd.steps,
            rate_hz=MIN_STEP_RATE_HZ,
            timeout_s=cmd.timeout_s,
        )

        if actual < cmd.steps:
            self._errors.add_error(
                ErrorCode.FOCUS_TIMEOUT,
                f"Focus timeout: {actual}/{cmd.steps} steps",
            )
            # Update position with what we actually moved
            moved = actual if cmd.direction == FOCUS_IN else -actual
            self._position += moved
        else:
            self._position = new_position

        self._state.set_focus_position(self._position)
        self._state.set_status(StatusCode.IDLE)
        return actual == cmd.steps
