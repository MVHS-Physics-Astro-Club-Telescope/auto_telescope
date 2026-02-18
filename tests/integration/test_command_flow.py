import pytest

from shared.commands.focus_command import FOCUS_IN
from shared.enums.status_codes import StatusCode
from tests.integration.conftest import wait_for_condition


class TestCommandFlow:
    def test_move_command_roundtrip(self, harness):
        """send_move -> Pi acks -> motors step -> position updated."""
        cmd_id = harness.sender.send_move(45.0, 90.0)
        assert cmd_id is not None

        ack = harness.sender.wait_for_ack(cmd_id, timeout=2.0)
        assert ack is not None
        assert ack["command_id"] == cmd_id
        assert ack["message_type"] == "ack"

        assert wait_for_condition(
            lambda: harness.alt_motor.cumulative_steps > 0,
        )
        assert wait_for_condition(
            lambda: harness.state_mgr.get_position() == (45.0, 90.0),
        )

    def test_focus_command_roundtrip(self, harness):
        """send_focus -> Pi acks -> focus motor steps -> focus_position updated."""
        cmd_id = harness.sender.send_focus(FOCUS_IN, 100)
        assert cmd_id is not None

        ack = harness.sender.wait_for_ack(cmd_id, timeout=2.0)
        assert ack is not None
        assert ack["command_id"] == cmd_id
        assert ack["message_type"] == "ack"

        assert wait_for_condition(
            lambda: harness.focus_motor.cumulative_steps > 0,
        )
        assert wait_for_condition(
            lambda: harness.state_mgr.get_snapshot().focus_position == 100,
        )

    def test_stop_command_roundtrip(self, harness):
        """send_stop -> Pi acks -> status returns to IDLE."""
        cmd_id = harness.sender.send_stop()
        assert cmd_id is not None

        ack = harness.sender.wait_for_ack(cmd_id, timeout=2.0)
        assert ack is not None
        assert ack["command_id"] == cmd_id

        assert wait_for_condition(
            lambda: harness.state_mgr.get_status() == StatusCode.IDLE,
        )

    def test_emergency_stop(self, harness):
        """send_stop(emergency=True) -> Pi enters EMERGENCY_STOP."""
        cmd_id = harness.sender.send_stop(emergency=True)
        assert cmd_id is not None

        ack = harness.sender.wait_for_ack(cmd_id, timeout=2.0)
        assert ack is not None

        assert wait_for_condition(
            lambda: harness.state_mgr.get_status() == StatusCode.EMERGENCY_STOP,
        )

    def test_status_request_triggers_state_report(self, harness):
        """send_status_request -> Pi sends state_report -> Host state updated."""
        assert not harness.host_state.has_state()

        ok = harness.sender.send_status_request()
        assert ok

        assert wait_for_condition(lambda: harness.host_state.has_state())

    def test_move_then_state_report(self, harness):
        """Key e2e: move -> execute -> state_report -> Host sees new position."""
        cmd_id = harness.sender.send_move(30.0, 120.0)
        ack = harness.sender.wait_for_ack(cmd_id, timeout=2.0)
        assert ack is not None

        # Wait for Pi to finish the move
        assert wait_for_condition(
            lambda: harness.state_mgr.get_position() == (30.0, 120.0),
        )

        # Trigger state report -> Host
        harness.send_state_report()

        assert wait_for_condition(
            lambda: harness.host_state.get_position() == (30.0, 120.0),
        )

    def test_focus_then_state_report(self, harness):
        """focus -> execute -> state_report -> Host sees focus_position."""
        cmd_id = harness.sender.send_focus(FOCUS_IN, 50)
        ack = harness.sender.wait_for_ack(cmd_id, timeout=2.0)
        assert ack is not None

        assert wait_for_condition(
            lambda: harness.state_mgr.get_snapshot().focus_position == 50,
        )

        harness.send_state_report()

        assert wait_for_condition(
            lambda: (
                harness.host_state.get_latest() is not None
                and harness.host_state.get_latest().focus_position == 50
            ),
        )

    def test_multiple_sequential_commands(self, harness):
        """3 moves in sequence, all acked, final position correct."""
        positions = [(10.0, 20.0), (30.0, 40.0), (50.0, 60.0)]

        for alt, az in positions:
            cmd_id = harness.sender.send_move(alt, az)
            assert cmd_id is not None
            ack = harness.sender.wait_for_ack(cmd_id, timeout=2.0)
            assert ack is not None
            assert wait_for_condition(
                lambda a=alt, z=az: harness.state_mgr.get_position() == (a, z),
            )

        assert harness.state_mgr.get_position() == (50.0, 60.0)

    def test_command_ids_preserved(self, harness):
        """command_id in ack matches what Sender returned."""
        cmd_id = harness.sender.send_move(20.0, 40.0)
        assert cmd_id is not None

        ack = harness.sender.wait_for_ack(cmd_id, timeout=2.0)
        assert ack is not None
        assert ack["command_id"] == cmd_id

    def test_move_sets_status_moving(self, harness):
        """Pi status transitions through MOVING during a move command."""
        assert harness.state_mgr.get_status() == StatusCode.IDLE

        cmd_id = harness.sender.send_move(10.0, 20.0)
        ack = harness.sender.wait_for_ack(cmd_id, timeout=2.0)
        assert ack is not None

        assert wait_for_condition(
            lambda: harness.state_mgr.get_position() == (10.0, 20.0),
        )

        # StatusRecorder captured the MOVING transition
        assert StatusCode.MOVING in harness.status_recorder.history
        # Final state is IDLE
        assert harness.state_mgr.get_status() == StatusCode.IDLE
