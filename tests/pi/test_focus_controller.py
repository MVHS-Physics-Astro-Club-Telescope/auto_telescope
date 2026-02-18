from shared.commands.focus_command import FocusCommand, FOCUS_IN, FOCUS_OUT
from shared.enums.status_codes import StatusCode
from shared.errors.error_codes import ErrorCode
from pi.config.constants import FOCUS_POSITION_MAX
from pi.control.focus_controller import FocusController
from pi.control.safety_manager import SafetyManager
from pi.hardware.motor_driver import MockMotorDriver
from pi.hardware.sensor_reader import MockSensorReader
from pi.state.error_state import ErrorState
from pi.state.telescope_state import TelescopeStateManager


def _make_focus_ctrl():
    error_state = ErrorState()
    state_mgr = TelescopeStateManager(error_state)
    sensors = MockSensorReader()
    focus_motor = MockMotorDriver()
    motors = [focus_motor]
    safety = SafetyManager(sensors, state_mgr, error_state, motors)
    ctrl = FocusController(focus_motor, safety, state_mgr, error_state)
    return ctrl, focus_motor, state_mgr, error_state


class TestFocusIn:
    def test_basic_focus_in(self):
        ctrl, motor, state_mgr, _ = _make_focus_ctrl()
        cmd = FocusCommand(direction=FOCUS_IN, steps=100)
        result = ctrl.execute_focus(cmd)
        assert result is True
        assert motor.cumulative_steps == 100
        snap = state_mgr.get_snapshot()
        assert snap.focus_position == 100

    def test_multiple_focus_in(self):
        ctrl, motor, state_mgr, _ = _make_focus_ctrl()
        ctrl.execute_focus(FocusCommand(direction=FOCUS_IN, steps=100))
        ctrl.execute_focus(FocusCommand(direction=FOCUS_IN, steps=50))
        snap = state_mgr.get_snapshot()
        assert snap.focus_position == 150


class TestFocusOut:
    def test_basic_focus_out(self):
        ctrl, _, state_mgr, _ = _make_focus_ctrl()
        ctrl.execute_focus(FocusCommand(direction=FOCUS_IN, steps=200))
        result = ctrl.execute_focus(FocusCommand(direction=FOCUS_OUT, steps=50))
        assert result is True
        snap = state_mgr.get_snapshot()
        assert snap.focus_position == 150


class TestFocusLimits:
    def test_reject_below_min(self):
        ctrl, _, _, error_state = _make_focus_ctrl()
        cmd = FocusCommand(direction=FOCUS_OUT, steps=100)
        result = ctrl.execute_focus(cmd)
        assert result is False
        assert ErrorCode.FOCUS_LIMIT_HIT in error_state.get_active_codes()

    def test_reject_above_max(self):
        ctrl, _, _, error_state = _make_focus_ctrl()
        cmd = FocusCommand(direction=FOCUS_IN, steps=FOCUS_POSITION_MAX + 1)
        result = ctrl.execute_focus(cmd)
        assert result is False
        assert ErrorCode.FOCUS_LIMIT_HIT in error_state.get_active_codes()


class TestFocusStateUpdate:
    def test_status_returns_to_idle(self):
        ctrl, _, state_mgr, _ = _make_focus_ctrl()
        cmd = FocusCommand(direction=FOCUS_IN, steps=10)
        ctrl.execute_focus(cmd)
        assert state_mgr.get_status() == StatusCode.IDLE
