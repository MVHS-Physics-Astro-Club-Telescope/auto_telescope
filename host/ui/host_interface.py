import sys
from typing import Optional

from host.comms.sender import Sender
from host.config.ui_params import PROMPT_STRING
from host.control.focus_controller import FocusController
from host.control.tracking_controller import TrackingController
from host.state.session_logs import SessionLog
from host.state.telescope_state import HostTelescopeState
from host.ui.display import format_log_entries, format_state, format_tracking_info
from host.utils.logger import get_logger

logger = get_logger("interface")

HELP_TEXT = """Commands:
  move <alt> <az> [speed]  - Slew to alt/az (speed 0.0-1.0, default 0.5)
  focus <in|out> <steps>   - Move focus motor
  stop [emergency]         - Stop movement (add 'emergency' for e-stop)
  track <name>             - Track a celestial object by name
  track stop               - Stop tracking
  autofocus                - Run autofocus routine
  status                   - Show telescope state
  tracking                 - Show tracking info
  log [count]              - Show recent log entries
  help                     - Show this help
  quit                     - Exit"""


class HostInterface:
    """CLI interface for the telescope operator."""

    def __init__(
        self,
        sender: Sender,
        tracking: TrackingController,
        focus: FocusController,
        telescope_state: HostTelescopeState,
        session_log: SessionLog,
    ) -> None:
        self._sender = sender
        self._tracking = tracking
        self._focus = focus
        self._state = telescope_state
        self._log = session_log
        self._running = False

    def run(self) -> None:
        self._running = True
        print(HELP_TEXT)

        while self._running:
            try:
                line = input(PROMPT_STRING).strip()
            except (EOFError, KeyboardInterrupt):
                self._running = False
                break

            if not line:
                continue

            try:
                self._dispatch(line)
            except Exception as e:
                print("Error: %s" % e)
                logger.error("Command error: %s", e)

    def stop(self) -> None:
        self._running = False

    def _dispatch(self, line: str) -> None:
        parts = line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == "move":
            self._cmd_move(args)
        elif cmd == "focus":
            self._cmd_focus(args)
        elif cmd == "stop":
            self._cmd_stop(args)
        elif cmd == "track":
            self._cmd_track(args)
        elif cmd == "autofocus":
            self._cmd_autofocus()
        elif cmd == "status":
            self._cmd_status()
        elif cmd == "tracking":
            self._cmd_tracking()
        elif cmd == "log":
            self._cmd_log(args)
        elif cmd == "help":
            print(HELP_TEXT)
        elif cmd == "quit":
            self._running = False
        else:
            print("Unknown command: %s (type 'help' for commands)" % cmd)

    def _cmd_move(self, args: list) -> None:
        if len(args) < 2:
            print("Usage: move <alt> <az> [speed]")
            return
        alt = float(args[0])
        az = float(args[1])
        speed = float(args[2]) if len(args) > 2 else 0.5
        cmd_id = self._sender.send_move(alt, az, speed)
        if cmd_id:
            print("Move command sent (id=%s)" % cmd_id)
        else:
            print("Failed to send move command")

    def _cmd_focus(self, args: list) -> None:
        if len(args) < 2:
            print("Usage: focus <in|out> <steps>")
            return
        direction = args[0].lower()
        if direction not in ("in", "out"):
            print("Direction must be 'in' or 'out'")
            return
        steps = int(args[1])
        cmd_id = self._sender.send_focus(direction, steps)
        if cmd_id:
            print("Focus command sent (id=%s)" % cmd_id)
        else:
            print("Failed to send focus command")

    def _cmd_stop(self, args: list) -> None:
        emergency = len(args) > 0 and args[0].lower() == "emergency"
        cmd_id = self._sender.send_stop(emergency=emergency)
        if cmd_id:
            label = "Emergency stop" if emergency else "Stop"
            print("%s sent (id=%s)" % (label, cmd_id))
        else:
            print("Failed to send stop command")

    def _cmd_track(self, args: list) -> None:
        if not args:
            print("Usage: track <name> | track stop")
            return
        if args[0].lower() == "stop":
            self._tracking.stop_tracking()
            print("Tracking stopped")
        else:
            name = " ".join(args)
            ok = self._tracking.start_tracking(name)
            if ok:
                print("Now tracking: %s" % name)
            else:
                print("Failed to start tracking '%s'" % name)

    def _cmd_autofocus(self) -> None:
        print("Running autofocus...")
        improved = self._focus.run_autofocus()
        if improved:
            print("Autofocus improved focus position")
        else:
            print("Autofocus found no improvement")

    def _cmd_status(self) -> None:
        state = self._state.get_latest()
        print(format_state(state))

    def _cmd_tracking(self) -> None:
        info = self._tracking.get_tracking_info()
        print(format_tracking_info(info))

    def _cmd_log(self, args: list) -> None:
        count = int(args[0]) if args else 10
        entries = self._log.get_recent(count)
        print(format_log_entries(entries, count))
