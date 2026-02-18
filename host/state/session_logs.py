import threading
import time
from collections import deque
from typing import Deque, Dict, List, Optional

from host.utils.logger import get_logger

logger = get_logger("session_logs")


class LogEntry:
    """A single log entry with category, data, and timestamp."""

    def __init__(self, category: str, data: Dict) -> None:
        self.category = category
        self.data = data
        self.timestamp = time.time()

    def __repr__(self) -> str:
        return "LogEntry(%s, %s)" % (self.category, self.data)


class SessionLog:
    """Thread-safe circular buffer of log entries."""

    def __init__(self, max_entries: int = 1000) -> None:
        self._lock = threading.Lock()
        self._entries: Deque[LogEntry] = deque(maxlen=max_entries)
        self._max_entries = max_entries

    def log_command(self, command_type: str, details: Dict) -> None:
        entry = LogEntry("command", {"type": command_type, **details})
        with self._lock:
            self._entries.append(entry)
        logger.debug("Logged command: %s", command_type)

    def log_state(self, state_data: Dict) -> None:
        entry = LogEntry("state", state_data)
        with self._lock:
            self._entries.append(entry)

    def log_error(self, error_msg: str, details: Optional[Dict] = None) -> None:
        data = {"error": error_msg}
        if details:
            data.update(details)
        entry = LogEntry("error", data)
        with self._lock:
            self._entries.append(entry)
        logger.warning("Logged error: %s", error_msg)

    def get_recent(self, count: int = 10) -> List[LogEntry]:
        with self._lock:
            items = list(self._entries)
        return items[-count:]

    def get_by_category(self, category: str, count: int = 10) -> List[LogEntry]:
        with self._lock:
            items = list(self._entries)
        filtered = [e for e in items if e.category == category]
        return filtered[-count:]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)
