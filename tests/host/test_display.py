import pytest

from shared.enums.status_codes import StatusCode
from shared.state.telescope_state import TelescopeState
from host.state.session_logs import LogEntry, SessionLog
from host.ui.display import format_log_entries, format_state, format_tracking_info


class TestFormatState:
    def test_none_state(self):
        result = format_state(None)
        assert "No state" in result

    def test_basic_state(self):
        state = TelescopeState(
            current_alt_deg=45.123,
            current_az_deg=90.456,
            status=StatusCode.IDLE,
        )
        result = format_state(state)
        assert "45.1230" in result
        assert "90.4560" in result
        assert "idle" in result

    def test_state_with_target(self):
        state = TelescopeState(
            current_alt_deg=10.0,
            current_az_deg=20.0,
            status=StatusCode.MOVING,
            target_alt_deg=45.0,
            target_az_deg=90.0,
        )
        result = format_state(state)
        assert "Target" in result

    def test_state_with_errors(self):
        state = TelescopeState(
            current_alt_deg=0.0,
            current_az_deg=0.0,
            status=StatusCode.ERROR,
            error_codes=[10, 20],
        )
        result = format_state(state)
        assert "Errors" in result


class TestFormatTrackingInfo:
    def test_not_tracking(self):
        result = format_tracking_info({"tracking": False})
        assert "Not tracking" in result

    def test_tracking_active(self):
        info = {
            "tracking": True,
            "target": "Mars",
            "target_alt": 45.0,
            "target_az": 120.0,
            "error_deg": 0.5,
            "within_tolerance": False,
        }
        result = format_tracking_info(info)
        assert "Mars" in result
        assert "CORRECTING" in result


class TestFormatLogEntries:
    def test_empty_log(self):
        result = format_log_entries([])
        assert "No log" in result

    def test_with_entries(self):
        entries = [
            LogEntry("command", {"type": "move"}),
            LogEntry("error", {"msg": "fail"}),
        ]
        result = format_log_entries(entries)
        assert "command" in result
        assert "error" in result
