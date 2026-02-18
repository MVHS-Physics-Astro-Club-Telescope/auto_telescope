import queue
from unittest.mock import MagicMock, patch

import pytest

from shared.enums.status_codes import StatusCode
from shared.state.telescope_state import TelescopeState
from host.comms.sender import Sender
from host.control.tracking_controller import TrackingController
from host.state.session_logs import SessionLog
from host.state.telescope_state import HostTelescopeState


def _mock_resolver(name, lat, lon, elev):
    """Mock coordinate resolver that returns predictable values."""
    targets = {
        "mars": (45.0, 20.0, 45.0, 120.0, True),
        "sirius": (100.0, -16.0, 25.0, 180.0, True),
        "below_horizon": (0.0, 0.0, -10.0, 0.0, False),
    }
    key = name.lower()
    if key in targets:
        return targets[key]
    raise ValueError("Unknown object: %s" % name)


@pytest.fixture
def setup():
    sl = SessionLog()
    rq = queue.Queue()
    sender = MagicMock(spec=Sender)
    sender.send_move.return_value = "cmd-123"
    sender.send_stop.return_value = "stop-123"

    ts = HostTelescopeState()
    ts.update_from_pi(TelescopeState(
        current_alt_deg=40.0,
        current_az_deg=115.0,
        status=StatusCode.IDLE,
    ))

    tc = TrackingController(
        sender=sender,
        telescope_state=ts,
        session_log=sl,
        lat=37.0, lon=-122.0, elev=32.0,
        coordinate_resolver=_mock_resolver,
    )
    return tc, sender, ts, sl


class TestTrackingController:
    def test_start_tracking_success(self, setup):
        tc, sender, ts, sl = setup
        assert tc.start_tracking("Mars")
        assert tc.is_tracking

    def test_start_tracking_below_horizon(self, setup):
        tc, sender, ts, sl = setup
        assert not tc.start_tracking("below_horizon")
        assert not tc.is_tracking

    def test_start_tracking_unknown_object(self, setup):
        tc, sender, ts, sl = setup
        assert not tc.start_tracking("not_real_xyz")
        assert not tc.is_tracking

    def test_stop_tracking(self, setup):
        tc, sender, ts, sl = setup
        tc.start_tracking("Mars")
        tc.stop_tracking()
        assert not tc.is_tracking
        sender.send_stop.assert_called()

    def test_update_sends_move(self, setup):
        tc, sender, ts, sl = setup
        tc.start_tracking("Mars")
        tc.update()
        sender.send_move.assert_called()

    def test_update_no_move_when_not_tracking(self, setup):
        tc, sender, ts, sl = setup
        tc.update()
        sender.send_move.assert_not_called()

    def test_update_stops_when_target_sets(self, setup):
        tc, sender, ts, sl = setup
        call_count = {"n": 0}

        def resolver(name, lat, lon, elev):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return (45.0, 20.0, 45.0, 120.0, True)
            return (45.0, 20.0, -5.0, 120.0, False)

        tc._resolve = resolver
        tc.start_tracking("Mars")
        tc.update()
        assert not tc.is_tracking

    def test_get_tracking_info_not_tracking(self, setup):
        tc, sender, ts, sl = setup
        info = tc.get_tracking_info()
        assert info["tracking"] is False

    def test_get_tracking_info_while_tracking(self, setup):
        tc, sender, ts, sl = setup
        tc.start_tracking("Mars")
        info = tc.get_tracking_info()
        assert info["tracking"] is True
        assert info["target"] == "Mars"
        assert info["target_alt"] == pytest.approx(45.0)

    def test_update_within_tolerance_no_move(self, setup):
        tc, sender, ts, sl = setup
        ts.update_from_pi(TelescopeState(
            current_alt_deg=45.0,
            current_az_deg=120.0,
            status=StatusCode.IDLE,
        ))
        tc.start_tracking("Mars")
        sender.send_move.reset_mock()
        tc.update()
        sender.send_move.assert_not_called()

    def test_tracking_sets_state_target(self, setup):
        tc, sender, ts, sl = setup
        tc.start_tracking("Mars")
        assert ts.get_tracking_target() == "Mars"

    def test_stop_tracking_clears_state_target(self, setup):
        tc, sender, ts, sl = setup
        tc.start_tracking("Mars")
        tc.stop_tracking()
        assert ts.get_tracking_target() is None
