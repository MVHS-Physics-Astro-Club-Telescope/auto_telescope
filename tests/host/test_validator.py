import pytest

from shared.enums.command_types import CommandType
from host.comms.validator import (
    is_valid_command,
    validate_incoming_response,
    validate_outgoing_command,
)


class TestValidateOutgoing:
    def test_valid_move_command(self):
        data = {
            "command_type": CommandType.MOVE,
            "target_alt_deg": 45.0,
            "target_az_deg": 90.0,
            "speed": 0.5,
        }
        errors = validate_outgoing_command(data)
        assert errors == []

    def test_invalid_move_out_of_range(self):
        data = {
            "command_type": CommandType.MOVE,
            "target_alt_deg": 200.0,
            "target_az_deg": 90.0,
            "speed": 0.5,
        }
        errors = validate_outgoing_command(data)
        assert len(errors) > 0

    def test_is_valid_command_true(self):
        data = {
            "command_type": CommandType.STOP,
            "emergency": False,
        }
        assert is_valid_command(data)

    def test_is_valid_command_false(self):
        data = {
            "command_type": CommandType.MOVE,
            "target_alt_deg": -100.0,
            "target_az_deg": 0.0,
            "speed": 0.5,
        }
        assert not is_valid_command(data)


class TestValidateIncoming:
    def test_valid_ack(self):
        data = {"message_type": "ack", "command_id": "abc"}
        errors = validate_incoming_response(data)
        assert errors == []

    def test_unknown_message_type(self):
        data = {"message_type": "unknown"}
        errors = validate_incoming_response(data)
        assert len(errors) > 0
