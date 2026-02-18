import time
from typing import Optional

from host.utils.math_utils import clamp


class PIDController:
    """PID controller for tracking error correction."""

    def __init__(
        self,
        kp: float = 1.0,
        ki: float = 0.0,
        kd: float = 0.1,
        output_min: float = 0.0,
        output_max: float = 1.0,
    ) -> None:
        self._kp = kp
        self._ki = ki
        self._kd = kd
        self._output_min = output_min
        self._output_max = output_max
        self._integral = 0.0
        self._prev_error: Optional[float] = None
        self._prev_time: Optional[float] = None

    def compute(self, error: float) -> float:
        now = time.monotonic()

        if self._prev_time is None:
            dt = 0.0
        else:
            dt = now - self._prev_time

        # Proportional
        p_term = self._kp * error

        # Integral
        if dt > 0:
            self._integral += error * dt
        i_term = self._ki * self._integral

        # Derivative
        if self._prev_error is not None and dt > 0:
            d_term = self._kd * (error - self._prev_error) / dt
        else:
            d_term = 0.0

        self._prev_error = error
        self._prev_time = now

        output = p_term + i_term + d_term
        return clamp(output, self._output_min, self._output_max)

    def reset(self) -> None:
        self._integral = 0.0
        self._prev_error = None
        self._prev_time = None
