import queue
import threading
import time
from typing import Optional

from shared.commands.focus_command import FocusCommand, FOCUS_IN, FOCUS_OUT
from shared.commands.move_command import MoveCommand
from shared.commands.stop_command import StopCommand
from shared.enums.command_types import CommandType
from shared.enums.status_codes import StatusCode
from shared.state.telescope_state import TelescopeState
from host.utils.logger import get_logger

logger = get_logger("simulator")


class TelescopeSimulator:
    """In-process mock Pi for testing without TCP or real hardware."""

    def __init__(self, slew_speed_deg_per_s: float = 5.0) -> None:
        self._slew_speed = slew_speed_deg_per_s
        self._lock = threading.Lock()
        self._current_alt = 0.0
        self._current_az = 0.0
        self._target_alt: Optional[float] = None
        self._target_az: Optional[float] = None
        self._status = StatusCode.IDLE
        self._focus_position = 5000
        self._is_tracking = False
        self._state_queue: "queue.Queue[TelescopeState]" = queue.Queue()
        self._slew_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def send_command(self, data: dict) -> dict:
        cmd_type = data.get("command_type")
        cmd_id = data.get("command_id", "sim")

        if cmd_type == CommandType.MOVE:
            cmd = MoveCommand.from_dict(data)
            self._start_slew(cmd)
            return {"message_type": "ack", "command_id": cmd_id}

        elif cmd_type == CommandType.FOCUS:
            cmd = FocusCommand.from_dict(data)
            self._execute_focus(cmd)
            return {"message_type": "ack", "command_id": cmd_id}

        elif cmd_type == CommandType.STOP:
            cmd = StopCommand.from_dict(data)
            self._execute_stop(cmd)
            return {"message_type": "ack", "command_id": cmd_id}

        elif cmd_type == CommandType.STATUS_REQUEST:
            return self._build_state_report()

        return {
            "message_type": "error",
            "command_id": cmd_id,
            "error": "Unknown command: %s" % cmd_type,
        }

    def get_state(self) -> TelescopeState:
        with self._lock:
            return TelescopeState(
                current_alt_deg=self._current_alt,
                current_az_deg=self._current_az,
                status=self._status,
                target_alt_deg=self._target_alt,
                target_az_deg=self._target_az,
                focus_position=self._focus_position,
                is_tracking=self._is_tracking,
            )

    def get_state_queue(self) -> "queue.Queue[TelescopeState]":
        return self._state_queue

    def _start_slew(self, cmd: MoveCommand) -> None:
        self._stop_event.set()
        if self._slew_thread is not None and self._slew_thread.is_alive():
            self._slew_thread.join(timeout=1.0)

        with self._lock:
            self._target_alt = cmd.target_alt_deg
            self._target_az = cmd.target_az_deg
            self._status = StatusCode.MOVING

        self._stop_event = threading.Event()
        self._slew_thread = threading.Thread(
            target=self._slew_loop,
            args=(cmd.target_alt_deg, cmd.target_az_deg, cmd.speed),
            daemon=True,
        )
        self._slew_thread.start()

    def _slew_loop(
        self, target_alt: float, target_az: float, speed: float
    ) -> None:
        rate = self._slew_speed * speed
        dt = 0.05  # 20 Hz update

        while not self._stop_event.is_set():
            with self._lock:
                d_alt = target_alt - self._current_alt
                d_az = target_az - self._current_az
                if d_az > 180.0:
                    d_az -= 360.0
                elif d_az < -180.0:
                    d_az += 360.0

                dist = (d_alt ** 2 + d_az ** 2) ** 0.5
                if dist < 0.01:
                    self._current_alt = target_alt
                    self._current_az = target_az
                    self._status = StatusCode.IDLE
                    self._target_alt = None
                    self._target_az = None
                    state = self.get_state()
                    self._state_queue.put(state)
                    return

                step = min(rate * dt, dist)
                if dist > 0:
                    self._current_alt += d_alt / dist * step
                    self._current_az += d_az / dist * step

            state = self.get_state()
            self._state_queue.put(state)
            self._stop_event.wait(timeout=dt)

    def _execute_focus(self, cmd: FocusCommand) -> None:
        with self._lock:
            if cmd.direction == FOCUS_IN:
                self._focus_position = max(0, self._focus_position - cmd.steps)
            elif cmd.direction == FOCUS_OUT:
                self._focus_position = min(10000, self._focus_position + cmd.steps)
        logger.debug("Focus %s %d -> pos=%d", cmd.direction, cmd.steps, self._focus_position)

    def _execute_stop(self, cmd: StopCommand) -> None:
        self._stop_event.set()
        with self._lock:
            self._status = (
                StatusCode.EMERGENCY_STOP if cmd.emergency else StatusCode.IDLE
            )
            self._target_alt = None
            self._target_az = None
            self._is_tracking = False

    def _build_state_report(self) -> dict:
        state = self.get_state()
        data = state.to_dict()
        data["message_type"] = "state_report"
        return data
