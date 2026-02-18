import queue
from unittest.mock import MagicMock, patch
from io import StringIO

import pytest

from shared.enums.status_codes import StatusCode
from shared.state.telescope_state import TelescopeState
from host.comms.sender import Sender
from host.control.focus_controller import FocusController
from host.control.tracking_controller import TrackingController
from host.state.session_logs import SessionLog
from host.state.telescope_state import HostTelescopeState
from host.ui.host_interface import HostInterface


@pytest.fixture
def setup():
    sender = MagicMock(spec=Sender)
    sender.send_move.return_value = "cmd-1"
    sender.send_focus.return_value = "cmd-2"
    sender.send_stop.return_value = "cmd-3"

    tracking = MagicMock(spec=TrackingController)
    tracking.is_tracking = False
    tracking.start_tracking.return_value = True
    tracking.get_tracking_info.return_value = {"tracking": False}

    focus = MagicMock(spec=FocusController)
    focus.run_autofocus.return_value = True

    ts = HostTelescopeState()
    ts.update_from_pi(TelescopeState(
        current_alt_deg=0.0, current_az_deg=0.0, status=StatusCode.IDLE,
    ))
    sl = SessionLog()

    interface = HostInterface(sender, tracking, focus, ts, sl)
    return interface, sender, tracking, focus


class TestHostInterface:
    def test_dispatch_move(self, setup):
        interface, sender, tracking, focus = setup
        interface._dispatch("move 45.0 90.0 0.5")
        sender.send_move.assert_called_once_with(45.0, 90.0, 0.5)

    def test_dispatch_focus(self, setup):
        interface, sender, tracking, focus = setup
        interface._dispatch("focus in 100")
        sender.send_focus.assert_called_once_with("in", 100)

    def test_dispatch_stop(self, setup):
        interface, sender, tracking, focus = setup
        interface._dispatch("stop")
        sender.send_stop.assert_called_once_with(emergency=False)

    def test_dispatch_stop_emergency(self, setup):
        interface, sender, tracking, focus = setup
        interface._dispatch("stop emergency")
        sender.send_stop.assert_called_once_with(emergency=True)

    def test_dispatch_track(self, setup):
        interface, sender, tracking, focus = setup
        interface._dispatch("track Mars")
        tracking.start_tracking.assert_called_once_with("Mars")

    def test_dispatch_track_stop(self, setup):
        interface, sender, tracking, focus = setup
        interface._dispatch("track stop")
        tracking.stop_tracking.assert_called_once()

    def test_dispatch_autofocus(self, setup):
        interface, sender, tracking, focus = setup
        interface._dispatch("autofocus")
        focus.run_autofocus.assert_called_once()

    def test_dispatch_quit(self, setup):
        interface, sender, tracking, focus = setup
        interface._dispatch("quit")
        assert not interface._running

    def test_dispatch_unknown_command(self, setup, capsys):
        interface, sender, tracking, focus = setup
        interface._dispatch("xyzzy")
        captured = capsys.readouterr()
        assert "Unknown command" in captured.out

    def test_move_default_speed(self, setup):
        interface, sender, tracking, focus = setup
        interface._dispatch("move 10.0 20.0")
        sender.send_move.assert_called_once_with(10.0, 20.0, 0.5)
