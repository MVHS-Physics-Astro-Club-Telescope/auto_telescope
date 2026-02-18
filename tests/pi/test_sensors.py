from pi.hardware.sensor_reader import (
    LimitSwitchState,
    EncoderReading,
    MockSensorReader,
)


class TestLimitSwitchState:
    def test_default_all_clear(self):
        state = LimitSwitchState()
        assert not state.alt_low
        assert not state.alt_high
        assert not state.az_low
        assert not state.az_high
        assert not state.any_hit

    def test_any_hit_alt_low(self):
        state = LimitSwitchState(alt_low=True)
        assert state.any_hit

    def test_any_hit_alt_high(self):
        state = LimitSwitchState(alt_high=True)
        assert state.any_hit

    def test_any_hit_az_low(self):
        state = LimitSwitchState(az_low=True)
        assert state.any_hit

    def test_any_hit_az_high(self):
        state = LimitSwitchState(az_high=True)
        assert state.any_hit

    def test_multiple_hits(self):
        state = LimitSwitchState(alt_low=True, az_high=True)
        assert state.any_hit


class TestEncoderReading:
    def test_default_none(self):
        reading = EncoderReading()
        assert reading.alt_counts is None
        assert reading.az_counts is None

    def test_with_values(self):
        reading = EncoderReading(alt_counts=100, az_counts=200)
        assert reading.alt_counts == 100
        assert reading.az_counts == 200


class TestMockSensorReader:
    def test_default_limits_clear(self):
        reader = MockSensorReader()
        limits = reader.read_limit_switches()
        assert not limits.any_hit

    def test_set_limits(self):
        reader = MockSensorReader()
        reader.set_limits(alt_low=True)
        limits = reader.read_limit_switches()
        assert limits.alt_low
        assert limits.any_hit

    def test_default_encoders_none(self):
        reader = MockSensorReader()
        encoders = reader.read_encoders()
        assert encoders.alt_counts is None

    def test_set_encoders(self):
        reader = MockSensorReader()
        reader.set_encoders(alt_counts=500, az_counts=1000)
        encoders = reader.read_encoders()
        assert encoders.alt_counts == 500
        assert encoders.az_counts == 1000
