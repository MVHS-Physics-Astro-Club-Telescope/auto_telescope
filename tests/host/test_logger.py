import logging

import pytest

from host.utils.logger import get_logger, log_command_sent, log_error_code, log_state_received


class TestGetLogger:
    def test_returns_logger_with_host_prefix(self):
        lgr = get_logger("test_mod")
        assert lgr.name == "host.test_mod"

    def test_logger_has_handler(self):
        lgr = get_logger("handler_test")
        assert len(lgr.handlers) >= 1

    def test_no_duplicate_handlers(self):
        lgr = get_logger("dup_test")
        count_before = len(lgr.handlers)
        lgr2 = get_logger("dup_test")
        assert len(lgr2.handlers) == count_before

    def test_formatter_includes_host_tag(self):
        lgr = get_logger("fmt_test")
        handler = lgr.handlers[0]
        fmt = handler.formatter._fmt
        assert "[HOST]" in fmt


class TestLogHelpers:
    def test_log_command_sent(self, caplog):
        lgr = get_logger("cmd_test")
        with caplog.at_level(logging.DEBUG, logger="host.cmd_test"):
            log_command_sent(lgr, "move", {"alt": 45.0, "az": 90.0})
        assert "CMD_SENT" in caplog.text

    def test_log_state_received(self, caplog):
        lgr = get_logger("state_test")
        with caplog.at_level(logging.DEBUG, logger="host.state_test"):
            log_state_received(lgr, {"current_alt_deg": 1.0, "current_az_deg": 2.0, "status": "idle"})
        assert "STATE" in caplog.text

    def test_log_error_code(self, caplog):
        lgr = get_logger("err_test")
        with caplog.at_level(logging.DEBUG, logger="host.err_test"):
            log_error_code(lgr, 10)
        assert "ERROR 10" in caplog.text
