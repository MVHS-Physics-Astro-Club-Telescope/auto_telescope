import time

import pytest

from shared.enums.command_types import CommandType
from tests.integration.conftest import wait_for_condition


class TestErrorHandling:
    def test_invalid_command_gets_error(self, harness):
        """Out-of-range values -> Pi sends error response."""
        harness.send_raw({
            "command_type": CommandType.MOVE,
            "command_id": "bad-move-1",
            "target_alt_deg": -999.0,
            "target_az_deg": 180.0,
            "speed": 0.5,
            "timestamp": time.time(),
        })

        assert wait_for_condition(
            lambda: not harness.response_queue.empty(),
        )
        msg = harness.response_queue.get(timeout=1.0)
        assert msg["message_type"] == "error"

    def test_unknown_command_type_error(self, harness):
        """Unknown command_type -> error response."""
        harness.send_raw({
            "command_type": "teleport",
            "command_id": "unknown-cmd-1",
            "timestamp": time.time(),
        })

        assert wait_for_condition(
            lambda: not harness.response_queue.empty(),
        )
        msg = harness.response_queue.get(timeout=1.0)
        assert msg["message_type"] == "error"
        assert msg["command_id"] == "unknown-cmd-1"

    def test_error_contains_command_id(self, harness):
        """Error response carries the original command_id."""
        test_cmd_id = "error-test-42"
        harness.send_raw({
            "command_type": CommandType.MOVE,
            "command_id": test_cmd_id,
            "timestamp": time.time(),
            # Missing target_alt_deg / target_az_deg -> validation failure
        })

        assert wait_for_condition(
            lambda: not harness.response_queue.empty(),
        )
        msg = harness.response_queue.get(timeout=1.0)
        assert msg["message_type"] == "error"
        assert msg["command_id"] == test_cmd_id

    def test_receiver_survives_unknown_message_type(self, harness):
        """Host Receiver logs warning for unknown type and keeps running."""
        # Pi sends a message with an unknown message_type
        harness.tcp_client.send({
            "message_type": "alien_signal",
            "data": "beep boop",
        })

        time.sleep(0.1)

        # Receiver should still be alive
        assert harness.receiver.is_alive()

        # Confirm by running a real status request through
        ok = harness.sender.send_status_request()
        assert ok
        assert wait_for_condition(lambda: harness.host_state.has_state())

    def test_host_validation_rejects_before_send(self, harness):
        """send_move(999, 999) returns None — nothing reaches Pi."""
        cmd_id = harness.sender.send_move(999.0, 999.0)
        assert cmd_id is None

        time.sleep(0.1)
        assert harness.alt_motor.cumulative_steps == 0
