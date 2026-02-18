import threading
import time
from typing import Dict, List, Optional, Tuple

from pi.utils.logger import get_logger, log_error_code

logger = get_logger("error_state")


class ErrorState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active: Dict[int, str] = {}  # code -> detail
        self._log: List[Tuple[float, int, str]] = []

    def add_error(self, code: int, detail: str = "") -> None:
        with self._lock:
            if code not in self._active:
                log_error_code(logger, code)
            self._active[code] = detail
            self._log.append((time.time(), code, detail))

    def clear_error(self, code: int) -> None:
        with self._lock:
            self._active.pop(code, None)

    def clear_all(self) -> None:
        with self._lock:
            self._active.clear()

    def has_error(self) -> bool:
        with self._lock:
            return len(self._active) > 0

    def has_safety_error(self) -> bool:
        with self._lock:
            return any(70 <= code <= 79 for code in self._active)

    def get_active_codes(self) -> List[int]:
        with self._lock:
            return list(self._active.keys())

    def get_detail(self, code: int) -> Optional[str]:
        with self._lock:
            return self._active.get(code)
