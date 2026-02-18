from shared.commands.focus_command import FocusCommand
from shared.commands.move_command import MoveCommand
from shared.commands.stop_command import StopCommand
from shared.enums.command_types import CommandType
from shared.enums.status_codes import StatusCode
from shared.state.telescope_state import TelescopeState
from pi.comms.message_parser import (
    build_ack_response,
    build_error_response,
    build_state_response,
    is_status_request,
    parse_command,
)


class TestParseCommand:
    def test_parse_move(self):
        data = {
            "command_type": "move",
            "target_alt_deg": 45.0,
            "target_az_deg": 180.0,
            "speed": 0.5,
            "command_id": "test-1",
        }
        cmd = parse_command(data)
        assert isinstance(cmd, MoveCommand)
        assert cmd.target_alt_deg == 45.0
        assert cmd.target_az_deg == 180.0

    def test_parse_focus(self):
        data = {
            "command_type": "focus",
            "direction": "in",
            "steps": 100,
            "command_id": "test-2",
        }
        cmd = parse_command(data)
        assert isinstance(cmd, FocusCommand)
        assert cmd.direction == "in"
        assert cmd.steps == 100

    def test_parse_stop(self):
        data = {
            "command_type": "stop",
            "emergency": True,
            "reason": "test",
            "command_id": "test-3",
        }
        cmd = parse_command(data)
        assert isinstance(cmd, StopCommand)
        assert cmd.emergency is True

    def test_parse_unknown_returns_none(self):
        data = {"command_type": "unknown_cmd"}
        cmd = parse_command(data)
        assert cmd is None

    def test_parse_missing_type_returns_none(self):
        data = {"target_alt_deg": 45.0}
        cmd = parse_command(data)
        assert cmd is None


class TestIsStatusRequest:
    def test_status_request(self):
        assert is_status_request({"command_type": "status_request"}) is True

    def test_not_status_request(self):
        assert is_status_request({"command_type": "move"}) is False

    def test_missing_type(self):
        assert is_status_request({}) is False


class TestResponseBuilders:
    def test_build_state_response(self):
        state = TelescopeState(
            current_alt_deg=45.0,
            current_az_deg=180.0,
            status=StatusCode.IDLE,
        )
        resp = build_state_response(state)
        assert resp["message_type"] == "state_report"
        assert resp["current_alt_deg"] == 45.0
        assert resp["current_az_deg"] == 180.0
        assert resp["status"] == StatusCode.IDLE

    def test_build_ack_response(self):
        resp = build_ack_response("cmd-123")
        assert resp["message_type"] == "ack"
        assert resp["command_id"] == "cmd-123"
        assert "timestamp" in resp

    def test_build_error_response(self):
        resp = build_error_response("cmd-456", "something failed")
        assert resp["message_type"] == "error"
        assert resp["command_id"] == "cmd-456"
        assert resp["error"] == "something failed"
        assert "timestamp" in resp
