from shared.enums.status_codes import StatusCode
from shared.errors.error_codes import ErrorCode
from pi.control.safety_manager import SafetyManager
from pi.hardware.motor_driver import MockMotorDriver
from pi.hardware.sensor_reader import MockSensorReader
from pi.state.error_state import ErrorState
from pi.state.telescope_state import TelescopeStateManager


def _make_safety():
    error_state = ErrorState()
    state_mgr = TelescopeStateManager(error_state)
    sensors = MockSensorReader()
    alt_motor = MockMotorDriver()
    az_motor = MockMotorDriver()
    focus_motor = MockMotorDriver()
    motors = [alt_motor, az_motor, focus_motor]
    safety = SafetyManager(sensors, state_mgr, error_state, motors)
    return safety, sensors, state_mgr, error_state, motors


class TestSafetyCheck:
    def test_all_clear(self):
        safety, _, _, error_state, _ = _make_safety()
        safety.feed_watchdog()
        assert safety.check() is True
        assert not error_state.has_error()

    def test_limit_switch_triggers_emergency(self):
        safety, sensors, _, error_state, _ = _make_safety()
        safety.feed_watchdog()
        sensors.set_limits(alt_low=True)
        assert safety.check() is False
        assert ErrorCode.POSITION_LIMIT_HIT in error_state.get_active_codes()

    def test_position_out_of_bounds(self):
        safety, _, state_mgr, error_state, _ = _make_safety()
        safety.feed_watchdog()
        state_mgr.update_position(-10.0, 0.0)  # Below ALT_MIN_DEG (-5)
        assert safety.check() is False
        assert ErrorCode.SAFETY_LIMIT_EXCEEDED in error_state.get_active_codes()

    def test_watchdog_timeout(self):
        safety, _, state_mgr, error_state, _ = _make_safety()
        # Don't feed watchdog — let it expire
        import time
        safety._watchdog._timeout_s = 0.01
        time.sleep(0.02)
        assert safety.check() is False
        assert ErrorCode.SAFETY_WATCHDOG_TIMEOUT in error_state.get_active_codes()


class TestEmergencyStop:
    def test_stops_all_motors(self):
        safety, _, _, error_state, motors = _make_safety()
        for m in motors:
            m.enable()
        safety.emergency_stop("test")
        for m in motors:
            assert not m._enabled

    def test_sets_emergency_status(self):
        safety, _, state_mgr, _, _ = _make_safety()
        safety.emergency_stop("test reason")
        assert state_mgr.get_status() == StatusCode.EMERGENCY_STOP

    def test_adds_error_code(self):
        safety, _, _, error_state, _ = _make_safety()
        safety.emergency_stop("test")
        assert ErrorCode.SAFETY_EMERGENCY_STOP in error_state.get_active_codes()


class TestValidateMoveTarget:
    def test_valid_target(self):
        safety, _, _, _, _ = _make_safety()
        assert safety.validate_move_target(45.0, 180.0) is True

    def test_alt_too_low(self):
        safety, _, _, _, _ = _make_safety()
        assert safety.validate_move_target(-10.0, 180.0) is False

    def test_alt_too_high(self):
        safety, _, _, _, _ = _make_safety()
        assert safety.validate_move_target(100.0, 180.0) is False

    def test_az_too_low(self):
        safety, _, _, _, _ = _make_safety()
        assert safety.validate_move_target(45.0, -10.0) is False

    def test_az_too_high(self):
        safety, _, _, _, _ = _make_safety()
        assert safety.validate_move_target(45.0, 370.0) is False

    def test_boundary_values_accepted(self):
        safety, _, _, _, _ = _make_safety()
        assert safety.validate_move_target(-5.0, -5.0) is True
        assert safety.validate_move_target(95.0, 365.0) is True
