import pytest

from host.config.constants import (
    COMMAND_ACK_TIMEOUT_S,
    DEFAULT_OBSERVER_ELEV,
    DEFAULT_OBSERVER_LAT,
    DEFAULT_OBSERVER_LON,
    FOCUS_SEARCH_STEPS,
    MAX_COMMAND_RETRIES,
    PI_HEARTBEAT_TIMEOUT_S,
    PID_KD,
    PID_KI,
    PID_KP,
    SERVER_HOST,
    SERVER_PORT,
    TRACKING_LOOP_HZ,
    TRACKING_TOLERANCE_DEG,
)


class TestConstants:
    def test_server_port_in_valid_range(self):
        assert 1024 <= SERVER_PORT <= 65535

    def test_tracking_hz_positive(self):
        assert TRACKING_LOOP_HZ > 0

    def test_pid_gains_non_negative(self):
        assert PID_KP >= 0
        assert PID_KI >= 0
        assert PID_KD >= 0

    def test_focus_search_steps_descending(self):
        for i in range(len(FOCUS_SEARCH_STEPS) - 1):
            assert FOCUS_SEARCH_STEPS[i] > FOCUS_SEARCH_STEPS[i + 1]

    def test_observer_location_valid(self):
        assert -90 <= DEFAULT_OBSERVER_LAT <= 90
        assert -180 <= DEFAULT_OBSERVER_LON <= 180
        assert DEFAULT_OBSERVER_ELEV >= 0
