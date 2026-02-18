import time

import pytest

from pi.utils.timer import LoopTimer, Timeout, monotonic_ms


class TestMonotonicMs:
    def test_returns_milliseconds(self):
        ms = monotonic_ms()
        assert ms > 0
        assert ms == pytest.approx(time.monotonic() * 1000.0, abs=50)


class TestLoopTimer:
    def test_tick_returns_positive_dt(self):
        timer = LoopTimer(target_hz=100)
        dt = timer.tick()
        assert dt > 0

    def test_tick_enforces_rate(self):
        hz = 50
        timer = LoopTimer(target_hz=hz)
        expected_period = 1.0 / hz

        dts = []
        for _ in range(5):
            dts.append(timer.tick())

        avg_dt = sum(dts) / len(dts)
        assert avg_dt == pytest.approx(expected_period, abs=0.01)

    def test_tick_handles_slow_iteration(self):
        timer = LoopTimer(target_hz=100)
        time.sleep(0.05)  # Simulate slow work
        dt = timer.tick()
        assert dt >= 0.04  # Should not sleep since we're already behind


class TestTimeout:
    def test_not_expired_initially(self):
        timeout = Timeout(1.0)
        assert not timeout.is_expired()

    def test_expired_after_duration(self):
        timeout = Timeout(0.01)
        time.sleep(0.02)
        assert timeout.is_expired()

    def test_remaining_decreases(self):
        timeout = Timeout(1.0)
        r1 = timeout.remaining_s()
        time.sleep(0.05)
        r2 = timeout.remaining_s()
        assert r2 < r1

    def test_remaining_never_negative(self):
        timeout = Timeout(0.01)
        time.sleep(0.02)
        assert timeout.remaining_s() == 0.0

    def test_reset_restarts_timer(self):
        timeout = Timeout(0.02)
        time.sleep(0.03)
        assert timeout.is_expired()
        timeout.reset()
        assert not timeout.is_expired()
        assert timeout.remaining_s() > 0
