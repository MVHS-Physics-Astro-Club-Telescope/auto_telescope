import pytest

from shared.enums.status_codes import StatusCode
from shared.errors.error_codes import ErrorCode
from tests.integration.conftest import wait_for_condition


class TestStateReporting:
    def test_state_report_updates_host_position(self, harness):
        """Manual position change on Pi -> state_report -> Host sees it."""
        harness.state_mgr.update_position(25.0, 150.0)
        harness.send_state_report()

        assert wait_for_condition(
            lambda: harness.host_state.get_position() == (25.0, 150.0),
        )

    def test_state_report_includes_status(self, harness):
        """Pi status propagates to Host."""
        harness.state_mgr.set_status(StatusCode.MOVING)
        harness.send_state_report()

        assert wait_for_condition(
            lambda: harness.host_state.get_status() == StatusCode.MOVING,
        )

    def test_state_report_includes_focus(self, harness):
        """Focus position propagates."""
        harness.state_mgr.set_focus_position(42)
        harness.send_state_report()

        assert wait_for_condition(
            lambda: (
                harness.host_state.get_latest() is not None
                and harness.host_state.get_latest().focus_position == 42
            ),
        )

    def test_state_report_includes_errors(self, harness):
        """Error codes propagate."""
        harness.error_state.add_error(ErrorCode.MOTOR_TIMEOUT, "test")
        harness.send_state_report()

        assert wait_for_condition(
            lambda: (
                harness.host_state.get_latest() is not None
                and ErrorCode.MOTOR_TIMEOUT
                in harness.host_state.get_latest().error_codes
            ),
        )

    def test_multiple_state_reports(self, harness):
        """3 sequential reports, Host tracks each."""
        positions = [(10.0, 20.0), (30.0, 40.0), (50.0, 60.0)]

        for alt, az in positions:
            harness.state_mgr.update_position(alt, az)
            harness.send_state_report()
            assert wait_for_condition(
                lambda a=alt, z=az: harness.host_state.get_position() == (a, z),
            )

    def test_state_report_logged(self, harness):
        """Session log contains state entry after a state report."""
        harness.state_mgr.update_position(15.0, 75.0)
        harness.send_state_report()

        assert wait_for_condition(lambda: harness.host_state.has_state())

        state_entries = harness.session_log.get_by_category("state")
        assert len(state_entries) > 0
