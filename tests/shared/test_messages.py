import json
import socket
import struct
import unittest.mock

import pytest

from shared.enums.command_types import CommandType
from shared.enums.status_codes import StatusCode
from shared.errors.error_codes import ErrorCode, get_error_description, ERROR_DESCRIPTIONS
from shared.commands.move_command import MoveCommand
from shared.commands.focus_command import FocusCommand, FOCUS_IN, FOCUS_OUT
from shared.commands.stop_command import StopCommand
from shared.state.telescope_state import TelescopeState
from shared.state.camera_state import CameraState
from shared.protocols.constants import (
    DEFAULT_PORT, HEADER_SIZE, MAX_MESSAGE_SIZE,
    ALT_MIN_DEG, ALT_MAX_DEG, AZ_MIN_DEG, AZ_MAX_DEG,
    SPEED_MIN, SPEED_MAX, FOCUS_STEPS_MIN, FOCUS_STEPS_MAX,
    DEFAULT_COMMAND_TIMEOUT_S,
)
from shared.protocols.message_validator import (
    validate_move_command, validate_focus_command, validate_stop_command,
    validate_message, ValidationError,
)
from shared.protocols.tcp_protocol import (
    encode_message, decode_header, decode_payload,
    send_message, recv_message, ProtocolError,
)


# ── Enum Tests ──────────────────────────────────────────────────────

class TestCommandType:
    def test_values(self):
        assert CommandType.MOVE == "move"
        assert CommandType.FOCUS == "focus"
        assert CommandType.STOP == "stop"
        assert CommandType.STATUS_REQUEST == "status_request"

    def test_is_str_enum(self):
        assert isinstance(CommandType.MOVE, str)

    def test_member_count(self):
        assert len(CommandType) == 4


class TestStatusCode:
    def test_values(self):
        assert StatusCode.OK == "ok"
        assert StatusCode.BUSY == "busy"
        assert StatusCode.ERROR == "error"
        assert StatusCode.MOVING == "moving"
        assert StatusCode.FOCUSING == "focusing"
        assert StatusCode.IDLE == "idle"
        assert StatusCode.EMERGENCY_STOP == "emergency_stop"

    def test_is_str_enum(self):
        assert isinstance(StatusCode.IDLE, str)

    def test_member_count(self):
        assert len(StatusCode) == 7


class TestErrorCode:
    def test_motor_range(self):
        assert ErrorCode.MOTOR_STALL == 10
        assert ErrorCode.MOTOR_NOT_INITIALIZED == 13

    def test_safety_range(self):
        assert ErrorCode.SAFETY_LIMIT_EXCEEDED == 70
        assert ErrorCode.SAFETY_WATCHDOG_TIMEOUT == 72

    def test_descriptions_complete(self):
        for code in ErrorCode:
            assert code in ERROR_DESCRIPTIONS

    def test_get_error_description_known(self):
        desc = get_error_description(ErrorCode.MOTOR_STALL)
        assert "stall" in desc.lower()

    def test_get_error_description_unknown(self):
        desc = get_error_description(999)
        assert "Unknown" in desc


# ── Command Round-Trip Tests ────────────────────────────────────────

class TestMoveCommand:
    def test_create_defaults(self):
        cmd = MoveCommand(target_alt_deg=45.0, target_az_deg=180.0)
        assert cmd.target_alt_deg == 45.0
        assert cmd.target_az_deg == 180.0
        assert cmd.speed == 0.5
        assert cmd.timeout_s == DEFAULT_COMMAND_TIMEOUT_S
        assert cmd.command_type == CommandType.MOVE
        assert cmd.command_id is not None
        assert cmd.timestamp > 0

    def test_round_trip(self):
        cmd = MoveCommand(target_alt_deg=30.0, target_az_deg=270.0, speed=0.8)
        d = cmd.to_dict()
        restored = MoveCommand.from_dict(d)
        assert restored.target_alt_deg == cmd.target_alt_deg
        assert restored.target_az_deg == cmd.target_az_deg
        assert restored.speed == cmd.speed
        assert restored.command_id == cmd.command_id
        assert restored.timestamp == cmd.timestamp

    def test_to_dict_has_command_type(self):
        cmd = MoveCommand(target_alt_deg=0.0, target_az_deg=0.0)
        d = cmd.to_dict()
        assert d["command_type"] == CommandType.MOVE

    def test_from_dict_with_custom_id(self):
        d = {"target_alt_deg": 10, "target_az_deg": 20, "command_id": "test-123"}
        cmd = MoveCommand.from_dict(d)
        assert cmd.command_id == "test-123"


class TestFocusCommand:
    def test_create(self):
        cmd = FocusCommand(direction=FOCUS_IN, steps=100)
        assert cmd.direction == "in"
        assert cmd.steps == 100
        assert cmd.command_type == CommandType.FOCUS

    def test_round_trip(self):
        cmd = FocusCommand(direction=FOCUS_OUT, steps=500)
        d = cmd.to_dict()
        restored = FocusCommand.from_dict(d)
        assert restored.direction == cmd.direction
        assert restored.steps == cmd.steps
        assert restored.command_id == cmd.command_id

    def test_focus_direction_constants(self):
        assert FOCUS_IN == "in"
        assert FOCUS_OUT == "out"


class TestStopCommand:
    def test_create_defaults(self):
        cmd = StopCommand()
        assert cmd.emergency is False
        assert cmd.reason == ""
        assert cmd.command_type == CommandType.STOP

    def test_emergency_stop(self):
        cmd = StopCommand(emergency=True, reason="obstacle detected")
        assert cmd.emergency is True
        assert cmd.reason == "obstacle detected"

    def test_round_trip(self):
        cmd = StopCommand(emergency=True, reason="test")
        d = cmd.to_dict()
        restored = StopCommand.from_dict(d)
        assert restored.emergency == cmd.emergency
        assert restored.reason == cmd.reason


# ── State Round-Trip Tests ──────────────────────────────────────────

class TestTelescopeState:
    def test_create_required_fields(self):
        state = TelescopeState(
            current_alt_deg=45.0,
            current_az_deg=180.0,
            status=StatusCode.IDLE,
        )
        assert state.current_alt_deg == 45.0
        assert state.current_az_deg == 180.0
        assert state.status == StatusCode.IDLE
        assert state.target_alt_deg is None
        assert state.error_codes == []
        assert state.is_tracking is False

    def test_round_trip(self):
        state = TelescopeState(
            current_alt_deg=30.0,
            current_az_deg=270.0,
            status=StatusCode.MOVING,
            target_alt_deg=45.0,
            target_az_deg=180.0,
            error_codes=[10, 20],
            focus_position=500,
            is_tracking=True,
        )
        d = state.to_dict()
        restored = TelescopeState.from_dict(d)
        assert restored.current_alt_deg == state.current_alt_deg
        assert restored.target_alt_deg == state.target_alt_deg
        assert restored.error_codes == state.error_codes
        assert restored.focus_position == state.focus_position
        assert restored.is_tracking is True

    def test_from_dict_missing_optionals(self):
        d = {"current_alt_deg": 10, "current_az_deg": 20, "status": "idle"}
        state = TelescopeState.from_dict(d)
        assert state.target_alt_deg is None
        assert state.error_codes == []


class TestCameraState:
    def test_defaults(self):
        state = CameraState()
        assert state.is_connected is False
        assert state.status == StatusCode.IDLE
        assert state.exposure_ms is None

    def test_round_trip(self):
        state = CameraState(
            is_connected=True,
            status=StatusCode.OK,
            exposure_ms=100.0,
            gain=2.5,
            temperature_c=-10.0,
        )
        d = state.to_dict()
        restored = CameraState.from_dict(d)
        assert restored.is_connected is True
        assert restored.exposure_ms == 100.0
        assert restored.gain == 2.5
        assert restored.temperature_c == -10.0


# ── Validation Tests ────────────────────────────────────────────────

class TestValidateMoveCommand:
    def test_valid(self):
        data = {"target_alt_deg": 45.0, "target_az_deg": 180.0, "speed": 0.5}
        errors = validate_move_command(data)
        assert errors == []

    def test_missing_alt(self):
        data = {"target_az_deg": 180.0}
        errors = validate_move_command(data)
        assert any("target_alt_deg" in e for e in errors)

    def test_missing_az(self):
        data = {"target_alt_deg": 45.0}
        errors = validate_move_command(data)
        assert any("target_az_deg" in e for e in errors)

    def test_alt_out_of_range_low(self):
        data = {"target_alt_deg": -1.0, "target_az_deg": 180.0}
        errors = validate_move_command(data)
        assert any("target_alt_deg" in e for e in errors)

    def test_alt_out_of_range_high(self):
        data = {"target_alt_deg": 91.0, "target_az_deg": 180.0}
        errors = validate_move_command(data)
        assert any("target_alt_deg" in e for e in errors)

    def test_az_out_of_range(self):
        data = {"target_alt_deg": 45.0, "target_az_deg": 361.0}
        errors = validate_move_command(data)
        assert any("target_az_deg" in e for e in errors)

    def test_speed_out_of_range(self):
        data = {"target_alt_deg": 45.0, "target_az_deg": 180.0, "speed": 1.5}
        errors = validate_move_command(data)
        assert any("speed" in e for e in errors)

    def test_boundary_values_valid(self):
        data = {"target_alt_deg": 0.0, "target_az_deg": 0.0, "speed": 0.0}
        assert validate_move_command(data) == []
        data = {"target_alt_deg": 90.0, "target_az_deg": 360.0, "speed": 1.0}
        assert validate_move_command(data) == []

    def test_non_numeric_alt(self):
        data = {"target_alt_deg": "abc", "target_az_deg": 180.0}
        errors = validate_move_command(data)
        assert any("numeric" in e for e in errors)


class TestValidateFocusCommand:
    def test_valid(self):
        data = {"direction": "in", "steps": 100}
        assert validate_focus_command(data) == []

    def test_missing_direction(self):
        data = {"steps": 100}
        errors = validate_focus_command(data)
        assert any("direction" in e for e in errors)

    def test_invalid_direction(self):
        data = {"direction": "left", "steps": 100}
        errors = validate_focus_command(data)
        assert any("direction" in e for e in errors)

    def test_steps_out_of_range(self):
        data = {"direction": "in", "steps": 0}
        errors = validate_focus_command(data)
        assert any("steps" in e for e in errors)

    def test_steps_too_high(self):
        data = {"direction": "out", "steps": 10001}
        errors = validate_focus_command(data)
        assert any("steps" in e for e in errors)


class TestValidateStopCommand:
    def test_valid_empty(self):
        assert validate_stop_command({}) == []

    def test_valid_with_fields(self):
        data = {"emergency": True, "reason": "test"}
        assert validate_stop_command(data) == []

    def test_invalid_emergency_type(self):
        data = {"emergency": "yes"}
        errors = validate_stop_command(data)
        assert any("emergency" in e for e in errors)


class TestValidateMessage:
    def test_dispatch_move(self):
        data = {
            "command_type": "move",
            "target_alt_deg": 45.0,
            "target_az_deg": 180.0,
        }
        errors = validate_message(data)
        assert errors == []

    def test_dispatch_focus(self):
        data = {"command_type": "focus", "direction": "in", "steps": 100}
        errors = validate_message(data)
        assert errors == []

    def test_dispatch_stop(self):
        data = {"command_type": "stop"}
        errors = validate_message(data)
        assert errors == []

    def test_dispatch_status_request(self):
        data = {"command_type": "status_request"}
        errors = validate_message(data)
        assert errors == []

    def test_missing_command_type(self):
        with pytest.raises(ValidationError, match="command_type"):
            validate_message({"target_alt_deg": 45.0})

    def test_unknown_command_type(self):
        with pytest.raises(ValidationError, match="Unknown"):
            validate_message({"command_type": "explode"})

    def test_not_a_dict(self):
        with pytest.raises(ValidationError, match="dict"):
            validate_message("not a dict")


# ── Protocol Encode/Decode Tests ────────────────────────────────────

class TestProtocolEncodeDecode:
    def test_encode_decode_round_trip(self):
        data = {"command_type": "move", "target_alt_deg": 45.0, "target_az_deg": 180.0}
        raw = encode_message(data)
        # First 4 bytes are header
        assert len(raw) > HEADER_SIZE
        length = decode_header(raw[:HEADER_SIZE])
        payload = decode_payload(raw[HEADER_SIZE:])
        assert payload == data
        assert length == len(raw) - HEADER_SIZE

    def test_header_format(self):
        data = {"test": True}
        raw = encode_message(data)
        expected_payload = json.dumps(data).encode("utf-8")
        expected_header = struct.pack("!I", len(expected_payload))
        assert raw[:4] == expected_header

    def test_oversized_message(self):
        data = {"big": "x" * (MAX_MESSAGE_SIZE + 1)}
        with pytest.raises(ProtocolError, match="exceeds maximum"):
            encode_message(data)

    def test_decode_header_wrong_size(self):
        with pytest.raises(ProtocolError, match="Header"):
            decode_header(b"\x00\x00")

    def test_decode_header_too_large_payload(self):
        header = struct.pack("!I", MAX_MESSAGE_SIZE + 1)
        with pytest.raises(ProtocolError, match="exceeds maximum"):
            decode_header(header)

    def test_decode_payload_invalid_json(self):
        with pytest.raises(ProtocolError, match="decode"):
            decode_payload(b"not json")

    def test_decode_payload_not_object(self):
        with pytest.raises(ProtocolError, match="JSON object"):
            decode_payload(json.dumps([1, 2, 3]).encode())


class TestSendRecvMessage:
    def _make_socket_pair(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", port))
        conn, _ = server.accept()

        server.close()
        return client, conn

    def test_send_recv_round_trip(self):
        client, conn = self._make_socket_pair()
        try:
            data = {"command_type": "stop", "emergency": True}
            send_message(client, data)
            received = recv_message(conn)
            assert received == data
        finally:
            client.close()
            conn.close()

    def test_recv_clean_close(self):
        client, conn = self._make_socket_pair()
        try:
            client.close()
            result = recv_message(conn)
            assert result is None
        finally:
            conn.close()

    def test_multiple_messages(self):
        client, conn = self._make_socket_pair()
        try:
            msgs = [
                {"command_type": "move", "target_alt_deg": i, "target_az_deg": i * 2}
                for i in range(5)
            ]
            for msg in msgs:
                send_message(client, msg)
            for msg in msgs:
                received = recv_message(conn)
                assert received == msg
        finally:
            client.close()
            conn.close()

    def test_recv_partial_close_raises(self):
        client, conn = self._make_socket_pair()
        try:
            # Send just a header with no payload
            header = struct.pack("!I", 100)
            client.sendall(header)
            client.close()
            with pytest.raises(ProtocolError, match="closed"):
                recv_message(conn)
        finally:
            conn.close()


# ── Constants Sanity Tests ──────────────────────────────────────────

class TestConstants:
    def test_default_port(self):
        assert DEFAULT_PORT == 5050

    def test_header_size(self):
        assert HEADER_SIZE == 4

    def test_max_message_size(self):
        assert MAX_MESSAGE_SIZE == 65536

    def test_alt_range(self):
        assert ALT_MIN_DEG == 0.0
        assert ALT_MAX_DEG == 90.0

    def test_az_range(self):
        assert AZ_MIN_DEG == 0.0
        assert AZ_MAX_DEG == 360.0

    def test_speed_range(self):
        assert SPEED_MIN == 0.0
        assert SPEED_MAX == 1.0

    def test_focus_range(self):
        assert FOCUS_STEPS_MIN == 1
        assert FOCUS_STEPS_MAX == 10000

    def test_default_timeout(self):
        assert DEFAULT_COMMAND_TIMEOUT_S == 30.0
