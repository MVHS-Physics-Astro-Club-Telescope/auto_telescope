from shared.enums.status_codes import StatusCode
from shared.errors.error_codes import ErrorCode
from shared.state.telescope_state import TelescopeState
from pi.state.error_state import ErrorState
from pi.state.telescope_state import TelescopeStateManager


class TestErrorState:
    def test_initially_no_errors(self):
        es = ErrorState()
        assert not es.has_error()
        assert es.get_active_codes() == []

    def test_add_error(self):
        es = ErrorState()
        es.add_error(ErrorCode.MOTOR_STALL, "stalled")
        assert es.has_error()
        assert ErrorCode.MOTOR_STALL in es.get_active_codes()

    def test_clear_error(self):
        es = ErrorState()
        es.add_error(ErrorCode.MOTOR_STALL)
        es.clear_error(ErrorCode.MOTOR_STALL)
        assert not es.has_error()

    def test_clear_all(self):
        es = ErrorState()
        es.add_error(ErrorCode.MOTOR_STALL)
        es.add_error(ErrorCode.COMMS_TIMEOUT)
        es.clear_all()
        assert not es.has_error()

    def test_deduplicates_active_errors(self):
        es = ErrorState()
        es.add_error(ErrorCode.MOTOR_STALL, "first")
        es.add_error(ErrorCode.MOTOR_STALL, "second")
        codes = es.get_active_codes()
        assert codes.count(ErrorCode.MOTOR_STALL) == 1
        assert es.get_detail(ErrorCode.MOTOR_STALL) == "second"

    def test_has_safety_error(self):
        es = ErrorState()
        es.add_error(ErrorCode.MOTOR_STALL)
        assert not es.has_safety_error()
        es.add_error(ErrorCode.SAFETY_EMERGENCY_STOP)
        assert es.has_safety_error()

    def test_safety_error_range(self):
        es = ErrorState()
        es.add_error(ErrorCode.SAFETY_LIMIT_EXCEEDED)
        assert es.has_safety_error()
        es.clear_all()
        es.add_error(ErrorCode.SAFETY_WATCHDOG_TIMEOUT)
        assert es.has_safety_error()


class TestTelescopeStateManager:
    def _make_manager(self):
        es = ErrorState()
        return TelescopeStateManager(es), es

    def test_initial_snapshot(self):
        mgr, _ = self._make_manager()
        snap = mgr.get_snapshot()
        assert isinstance(snap, TelescopeState)
        assert snap.current_alt_deg == 0.0
        assert snap.current_az_deg == 0.0
        assert snap.status == StatusCode.IDLE

    def test_update_position(self):
        mgr, _ = self._make_manager()
        mgr.update_position(45.0, 180.0)
        snap = mgr.get_snapshot()
        assert snap.current_alt_deg == 45.0
        assert snap.current_az_deg == 180.0

    def test_set_target(self):
        mgr, _ = self._make_manager()
        mgr.set_target(30.0, 90.0)
        snap = mgr.get_snapshot()
        assert snap.target_alt_deg == 30.0
        assert snap.target_az_deg == 90.0

    def test_set_status(self):
        mgr, _ = self._make_manager()
        mgr.set_status(StatusCode.MOVING)
        assert mgr.get_status() == StatusCode.MOVING
        snap = mgr.get_snapshot()
        assert snap.status == StatusCode.MOVING

    def test_set_focus_position(self):
        mgr, _ = self._make_manager()
        mgr.set_focus_position(500)
        snap = mgr.get_snapshot()
        assert snap.focus_position == 500

    def test_set_tracking(self):
        mgr, _ = self._make_manager()
        mgr.set_tracking(True)
        snap = mgr.get_snapshot()
        assert snap.is_tracking is True

    def test_errors_propagate_to_snapshot(self):
        mgr, es = self._make_manager()
        es.add_error(ErrorCode.MOTOR_STALL)
        snap = mgr.get_snapshot()
        assert ErrorCode.MOTOR_STALL in snap.error_codes

    def test_snapshot_returns_telescope_state_type(self):
        mgr, _ = self._make_manager()
        snap = mgr.get_snapshot()
        assert isinstance(snap, TelescopeState)
        d = snap.to_dict()
        assert "current_alt_deg" in d
        assert "status" in d
