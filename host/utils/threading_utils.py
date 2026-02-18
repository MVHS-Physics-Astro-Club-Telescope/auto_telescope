import threading
import time
from typing import Callable, Optional


class StoppableThread:
    """Thread wrapper with a stop event for clean shutdown."""

    def __init__(
        self,
        target: Callable[..., None],
        name: Optional[str] = None,
        daemon: bool = True,
    ) -> None:
        self._target = target
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._name = name
        self._daemon = daemon

    @property
    def stop_event(self) -> threading.Event:
        return self._stop_event

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._target,
            args=(self._stop_event,),
            name=self._name,
            daemon=self._daemon,
        )
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()


class PeriodicTask:
    """Runs a callable at a fixed rate in a background thread."""

    def __init__(
        self,
        target: Callable[[], None],
        hz: float,
        name: Optional[str] = None,
    ) -> None:
        self._target = target
        self._interval = 1.0 / hz if hz > 0 else 1.0
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._name = name

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name=self._name,
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            start = time.monotonic()
            try:
                self._target()
            except Exception:
                pass
            elapsed = time.monotonic() - start
            sleep_time = self._interval - elapsed
            if sleep_time > 0:
                self._stop_event.wait(timeout=sleep_time)
