import time

import pytest

from shared.enums.command_types import CommandType
from shared.enums.status_codes import StatusCode
from host.simulation.simulator import TelescopeSimulator


@pytest.fixture
def sim():
    return TelescopeSimulator(slew_speed_deg_per_s=100.0)


class TestTelescopeSimulator:
    def test_initial_state_idle(self, sim):
        state = sim.get_state()
        assert state.status == StatusCode.IDLE
        assert state.current_alt_deg == 0.0
        assert state.current_az_deg == 0.0

    def test_move_command_returns_ack(self, sim):
        resp = sim.send_command({
            "command_type": CommandType.MOVE,
            "target_alt_deg": 45.0,
            "target_az_deg": 90.0,
            "speed": 1.0,
            "command_id": "test-1",
            "timeout_s": 30.0,
        })
        assert resp["message_type"] == "ack"

    def test_focus_in(self, sim):
        initial = sim.get_state().focus_position
        sim.send_command({
            "command_type": CommandType.FOCUS,
            "direction": "in",
            "steps": 100,
            "command_id": "f-1",
            "timeout_s": 30.0,
        })
        state = sim.get_state()
        assert state.focus_position == initial - 100

    def test_focus_out(self, sim):
        initial = sim.get_state().focus_position
        sim.send_command({
            "command_type": CommandType.FOCUS,
            "direction": "out",
            "steps": 200,
            "command_id": "f-2",
            "timeout_s": 30.0,
        })
        state = sim.get_state()
        assert state.focus_position == initial + 200

    def test_stop_command(self, sim):
        sim.send_command({
            "command_type": CommandType.MOVE,
            "target_alt_deg": 80.0,
            "target_az_deg": 180.0,
            "speed": 0.5,
            "command_id": "m-1",
            "timeout_s": 30.0,
        })
        time.sleep(0.05)
        sim.send_command({
            "command_type": CommandType.STOP,
            "emergency": False,
            "command_id": "s-1",
            "reason": "",
            "timeout_s": 30.0,
        })
        time.sleep(0.1)
        state = sim.get_state()
        assert state.status == StatusCode.IDLE

    def test_emergency_stop(self, sim):
        sim.send_command({
            "command_type": CommandType.STOP,
            "emergency": True,
            "command_id": "es-1",
            "reason": "test",
            "timeout_s": 30.0,
        })
        state = sim.get_state()
        assert state.status == StatusCode.EMERGENCY_STOP

    def test_slew_moves_toward_target(self, sim):
        sim.send_command({
            "command_type": CommandType.MOVE,
            "target_alt_deg": 45.0,
            "target_az_deg": 90.0,
            "speed": 1.0,
            "command_id": "m-2",
            "timeout_s": 30.0,
        })
        time.sleep(0.3)
        state = sim.get_state()
        assert state.current_alt_deg > 0.0 or state.current_az_deg > 0.0

    def test_status_request(self, sim):
        resp = sim.send_command({
            "command_type": CommandType.STATUS_REQUEST,
        })
        assert resp["message_type"] == "state_report"
