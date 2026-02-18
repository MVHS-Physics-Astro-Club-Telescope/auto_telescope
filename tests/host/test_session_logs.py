import pytest

from host.state.session_logs import LogEntry, SessionLog


class TestLogEntry:
    def test_has_timestamp(self):
        entry = LogEntry("command", {"type": "move"})
        assert entry.timestamp > 0

    def test_stores_category_and_data(self):
        entry = LogEntry("error", {"msg": "fail"})
        assert entry.category == "error"
        assert entry.data == {"msg": "fail"}


class TestSessionLog:
    def test_log_command(self):
        log = SessionLog()
        log.log_command("move", {"alt": 45.0})
        assert len(log) == 1

    def test_log_state(self):
        log = SessionLog()
        log.log_state({"alt": 10.0})
        entries = log.get_recent(1)
        assert entries[0].category == "state"

    def test_log_error(self):
        log = SessionLog()
        log.log_error("test error")
        entries = log.get_recent(1)
        assert entries[0].category == "error"
        assert entries[0].data["error"] == "test error"

    def test_get_recent(self):
        log = SessionLog()
        for i in range(20):
            log.log_command("cmd_%d" % i, {})
        recent = log.get_recent(5)
        assert len(recent) == 5

    def test_get_by_category(self):
        log = SessionLog()
        log.log_command("move", {})
        log.log_error("err")
        log.log_command("stop", {})
        cmds = log.get_by_category("command")
        assert len(cmds) == 2

    def test_circular_buffer(self):
        log = SessionLog(max_entries=5)
        for i in range(10):
            log.log_command("cmd_%d" % i, {"i": i})
        assert len(log) == 5
        recent = log.get_recent(10)
        assert len(recent) == 5

    def test_clear(self):
        log = SessionLog()
        log.log_command("move", {})
        log.clear()
        assert len(log) == 0

    def test_log_error_with_details(self):
        log = SessionLog()
        log.log_error("fail", {"code": 10})
        entries = log.get_recent(1)
        assert entries[0].data["code"] == 10
