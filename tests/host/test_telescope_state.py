import time

import pytest

from shared.enums.status_codes import StatusCode
from shared.state.telescope_state import TelescopeState
from host.state.telescope_state import HostTelescopeState


@pytest.fixture
def state():
    return HostTelescopeState()


def _make_state(alt=10.0, az=20.0, status=StatusCode.IDLE):
    return TelescopeState(
        current_alt_deg=alt,
        current_az_deg=az,
        status=status,
    )


class TestHostTelescopeState:
    def test_initial_state_is_none(self, state):
        assert state.get_latest() is None
        assert not state.has_state()

    def test_update_from_pi(self, state):
        ts = _make_state(alt=45.0, az=90.0)
        state.update_from_pi(ts)
        assert state.has_state()
        latest = state.get_latest()
        assert latest.current_alt_deg == 45.0
        assert latest.current_az_deg == 90.0

    def test_get_position(self, state):
        assert state.get_position() is None
        ts = _make_state(alt=30.0, az=60.0)
        state.update_from_pi(ts)
        pos = state.get_position()
        assert pos == (30.0, 60.0)

    def test_get_status_default(self, state):
        assert state.get_status() == StatusCode.IDLE

    def test_get_status_after_update(self, state):
        ts = _make_state(status=StatusCode.MOVING)
        state.update_from_pi(ts)
        assert state.get_status() == StatusCode.MOVING

    def test_seconds_since_update_initial(self, state):
        assert state.seconds_since_update() == float("inf")

    def test_seconds_since_update_after_update(self, state):
        ts = _make_state()
        state.update_from_pi(ts)
        elapsed = state.seconds_since_update()
        assert elapsed < 1.0

    def test_set_tracking_target(self, state):
        state.set_tracking_target("Mars")
        assert state.get_tracking_target() == "Mars"

    def test_clear_tracking_target(self, state):
        state.set_tracking_target("Mars")
        state.clear_tracking_target()
        assert state.get_tracking_target() is None

    def test_multiple_updates_keeps_latest(self, state):
        state.update_from_pi(_make_state(alt=10.0, az=20.0))
        state.update_from_pi(_make_state(alt=50.0, az=100.0))
        latest = state.get_latest()
        assert latest.current_alt_deg == 50.0
        assert latest.current_az_deg == 100.0
