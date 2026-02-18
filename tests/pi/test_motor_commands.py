from shared.commands.move_command import MoveCommand
from shared.commands.stop_command import StopCommand
from shared.enums.status_codes import StatusCode
from shared.errors.error_codes import ErrorCode
from pi.config.constants import MIN_STEP_RATE_HZ, MAX_STEP_RATE_HZ, STEPS_PER_DEGREE_ALT
from pi.control.motor_controller import MotorController
from pi.control.safety_manager import SafetyManager
from pi.hardware.motor_driver import MockMotorDriver
from pi.hardware.sensor_reader import MockSensorReader
from pi.state.error_state import ErrorState
from pi.state.telescope_state import TelescopeStateManager


def _make_motor_ctrl():
    error_state = ErrorState()
    state_mgr = TelescopeStateManager(error_state)
    sensors = MockSensorReader()
    alt_motor = MockMotorDriver()
    az_motor = MockMotorDriver()
    focus_motor = MockMotorDriver()
    motors = [alt_motor, az_motor, focus_motor]
    safety = SafetyManager(sensors, state_mgr, error_state, motors)
    ctrl = MotorController(alt_motor, az_motor, safety, state_mgr, error_state)
    return ctrl, alt_motor, az_motor, state_mgr, error_state, safety


class TestExecuteMove:
    def test_basic_move(self):
        ctrl, alt, az, state_mgr, _, _ = _make_motor_ctrl()
        cmd = MoveCommand(target_alt_deg=10.0, target_az_deg=20.0, speed=0.5)
        result = ctrl.execute_move(cmd)
        assert result is True
        assert alt.cumulative_steps > 0
        assert az.cumulative_steps > 0

    def test_move_updates_position(self):
        ctrl, _, _, state_mgr, _, _ = _make_motor_ctrl()
        cmd = MoveCommand(target_alt_deg=10.0, target_az_deg=20.0)
        ctrl.execute_move(cmd)
        snap = state_mgr.get_snapshot()
        assert snap.current_alt_deg == 10.0
        assert snap.current_az_deg == 20.0

    def test_move_sets_idle_after_completion(self):
        ctrl, _, _, state_mgr, _, _ = _make_motor_ctrl()
        cmd = MoveCommand(target_alt_deg=10.0, target_az_deg=20.0)
        ctrl.execute_move(cmd)
        assert state_mgr.get_status() == StatusCode.IDLE

    def test_move_clears_target_after_completion(self):
        ctrl, _, _, state_mgr, _, _ = _make_motor_ctrl()
        cmd = MoveCommand(target_alt_deg=10.0, target_az_deg=20.0)
        ctrl.execute_move(cmd)
        snap = state_mgr.get_snapshot()
        assert snap.target_alt_deg is None
        assert snap.target_az_deg is None


class TestSpeedMapping:
    def test_speed_zero_gives_min_rate(self):
        rate = MotorController._speed_to_rate(0.0)
        assert rate == MIN_STEP_RATE_HZ

    def test_speed_one_gives_max_rate(self):
        rate = MotorController._speed_to_rate(1.0)
        assert rate == MAX_STEP_RATE_HZ

    def test_speed_half_gives_midpoint(self):
        rate = MotorController._speed_to_rate(0.5)
        expected = MIN_STEP_RATE_HZ + 0.5 * (MAX_STEP_RATE_HZ - MIN_STEP_RATE_HZ)
        assert rate == expected

    def test_speed_clamped_above_one(self):
        rate = MotorController._speed_to_rate(2.0)
        assert rate == MAX_STEP_RATE_HZ

    def test_speed_clamped_below_zero(self):
        rate = MotorController._speed_to_rate(-1.0)
        assert rate == MIN_STEP_RATE_HZ


class TestSafetyReject:
    def test_rejects_out_of_range_target(self):
        ctrl, _, _, _, error_state, _ = _make_motor_ctrl()
        cmd = MoveCommand(target_alt_deg=200.0, target_az_deg=0.0)
        result = ctrl.execute_move(cmd)
        assert result is False
        assert ErrorCode.POSITION_OUT_OF_RANGE in error_state.get_active_codes()


class TestStop:
    def test_stop_sets_idle(self):
        ctrl, _, _, state_mgr, _, _ = _make_motor_ctrl()
        cmd = StopCommand()
        ctrl.execute_stop(cmd)
        assert state_mgr.get_status() == StatusCode.IDLE

    def test_emergency_stop_sets_emergency(self):
        ctrl, _, _, state_mgr, error_state, _ = _make_motor_ctrl()
        cmd = StopCommand(emergency=True, reason="test emergency")
        ctrl.execute_stop(cmd)
        assert state_mgr.get_status() == StatusCode.EMERGENCY_STOP
        assert ErrorCode.SAFETY_EMERGENCY_STOP in error_state.get_active_codes()

    def test_stop_sets_stop_event(self):
        ctrl, _, _, _, _, _ = _make_motor_ctrl()
        cmd = StopCommand()
        ctrl.execute_stop(cmd)
        assert ctrl.stop_event.is_set()
