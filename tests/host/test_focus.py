import queue
from unittest.mock import MagicMock, call

import pytest

from shared.enums.status_codes import StatusCode
from shared.state.telescope_state import TelescopeState
from host.comms.sender import Sender
from host.control.focus_controller import FocusController
from host.state.session_logs import SessionLog
from host.state.telescope_state import HostTelescopeState


@pytest.fixture
def setup():
    sl = SessionLog()
    rq = queue.Queue()
    sender = MagicMock(spec=Sender)
    sender.send_focus.return_value = "focus-123"

    ts = HostTelescopeState()
    ts.update_from_pi(TelescopeState(
        current_alt_deg=0.0,
        current_az_deg=0.0,
        status=StatusCode.IDLE,
        focus_position=5000,
    ))

    fc = FocusController(sender=sender, telescope_state=ts, session_log=sl)
    return fc, sender, ts, sl


class TestFocusController:
    def test_autofocus_calls_send_focus(self, setup):
        fc, sender, ts, sl = setup
        fc.run_autofocus(step_sizes=[100])
        assert sender.send_focus.call_count > 0

    def test_autofocus_not_running_initially(self, setup):
        fc, sender, ts, sl = setup
        assert not fc.is_running

    def test_autofocus_not_running_after_complete(self, setup):
        fc, sender, ts, sl = setup
        fc.run_autofocus(step_sizes=[100])
        assert not fc.is_running

    def test_autofocus_with_no_state(self):
        sl = SessionLog()
        rq = queue.Queue()
        sender = MagicMock(spec=Sender)
        sender.send_focus.return_value = "f-1"
        ts = HostTelescopeState()
        fc = FocusController(sender=sender, telescope_state=ts, session_log=sl)
        result = fc.run_autofocus(step_sizes=[50])
        assert not result

    def test_autofocus_multiple_steps(self, setup):
        fc, sender, ts, sl = setup
        fc.run_autofocus(step_sizes=[100, 50])
        assert sender.send_focus.call_count >= 2

    def test_autofocus_logs_start_and_done(self, setup):
        fc, sender, ts, sl = setup
        fc.run_autofocus(step_sizes=[100])
        categories = [e.data.get("type") for e in sl.get_by_category("command")]
        assert "autofocus_start" in categories
        assert "autofocus_done" in categories

    def test_default_step_sizes_used(self, setup):
        fc, sender, ts, sl = setup
        fc.run_autofocus()
        assert sender.send_focus.call_count > 0

    def test_autofocus_returns_bool(self, setup):
        fc, sender, ts, sl = setup
        result = fc.run_autofocus(step_sizes=[100])
        assert isinstance(result, bool)
