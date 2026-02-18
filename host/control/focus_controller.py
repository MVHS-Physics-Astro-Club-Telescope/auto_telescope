from typing import List, Optional

from shared.commands.focus_command import FOCUS_IN, FOCUS_OUT
from host.comms.sender import Sender
from host.config.constants import FOCUS_METRIC_THRESHOLD, FOCUS_SEARCH_STEPS
from host.state.session_logs import SessionLog
from host.state.telescope_state import HostTelescopeState
from host.utils.logger import get_logger

logger = get_logger("focus_ctrl")


class FocusController:
    """Autofocus using coarse-to-fine search."""

    def __init__(
        self,
        sender: Sender,
        telescope_state: HostTelescopeState,
        session_log: SessionLog,
    ) -> None:
        self._sender = sender
        self._state = telescope_state
        self._session_log = session_log
        self._running = False
        self._best_metric: float = 0.0
        self._best_position: Optional[int] = None

    @property
    def is_running(self) -> bool:
        return self._running

    def run_autofocus(
        self, step_sizes: Optional[List[int]] = None
    ) -> bool:
        if step_sizes is None:
            step_sizes = list(FOCUS_SEARCH_STEPS)

        self._running = True
        self._best_metric = self._get_focus_metric()
        self._best_position = self._get_focus_position()
        improved = False

        logger.info("Autofocus started (steps=%s)", step_sizes)
        self._session_log.log_command("autofocus_start", {"steps": step_sizes})

        try:
            for step_size in step_sizes:
                got_better = self._search_step(step_size)
                if got_better:
                    improved = True
        finally:
            self._running = False

        logger.info(
            "Autofocus complete: improved=%s best_pos=%s metric=%.4f",
            improved, self._best_position, self._best_metric,
        )
        self._session_log.log_command(
            "autofocus_done",
            {"improved": improved, "best_position": self._best_position},
        )
        return improved

    def _search_step(self, step_size: int) -> bool:
        improved = False

        # Try focus in
        self._sender.send_focus(FOCUS_IN, step_size)
        metric_in = self._get_focus_metric()

        if metric_in > self._best_metric + FOCUS_METRIC_THRESHOLD:
            self._best_metric = metric_in
            self._best_position = self._get_focus_position()
            improved = True
            logger.debug("Focus IN by %d improved metric to %.4f", step_size, metric_in)
        else:
            # Undo and try out
            self._sender.send_focus(FOCUS_OUT, step_size)
            self._sender.send_focus(FOCUS_OUT, step_size)
            metric_out = self._get_focus_metric()

            if metric_out > self._best_metric + FOCUS_METRIC_THRESHOLD:
                self._best_metric = metric_out
                self._best_position = self._get_focus_position()
                improved = True
                logger.debug("Focus OUT by %d improved metric to %.4f", step_size, metric_out)
            else:
                # Return to original
                self._sender.send_focus(FOCUS_IN, step_size)

        return improved

    def _get_focus_metric(self) -> float:
        """Get current focus quality metric from telescope state.

        In production, this would analyze camera images (e.g. Laplacian variance).
        For now, uses focus_position as a proxy — closer to midrange is better.
        """
        state = self._state.get_latest()
        if state is None or state.focus_position is None:
            return 0.0
        pos = state.focus_position
        # Proxy: peak at midpoint of 0-10000 range
        return 1.0 - abs(pos - 5000) / 5000.0

    def _get_focus_position(self) -> Optional[int]:
        state = self._state.get_latest()
        if state is None:
            return None
        return state.focus_position
