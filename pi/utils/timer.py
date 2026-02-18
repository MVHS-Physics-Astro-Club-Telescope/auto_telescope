import time


def monotonic_ms() -> float:
    return time.monotonic() * 1000.0


class LoopTimer:
    def __init__(self, target_hz: float):
        self._period = 1.0 / target_hz
        self._last = time.monotonic()

    def tick(self) -> float:
        now = time.monotonic()
        dt = now - self._last
        sleep_time = self._period - dt
        if sleep_time > 0:
            time.sleep(sleep_time)
        now = time.monotonic()
        actual_dt = now - self._last
        self._last = now
        return actual_dt


class Timeout:
    def __init__(self, timeout_s: float):
        self._timeout_s = timeout_s
        self._start = time.monotonic()

    def is_expired(self) -> bool:
        return time.monotonic() - self._start >= self._timeout_s

    def remaining_s(self) -> float:
        remaining = self._timeout_s - (time.monotonic() - self._start)
        return max(0.0, remaining)

    def reset(self) -> None:
        self._start = time.monotonic()
