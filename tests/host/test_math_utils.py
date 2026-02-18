import pytest

from host.utils.math_utils import (
    alt_az_delta,
    angular_distance,
    arcsec_to_degrees,
    clamp,
    degrees_to_arcsec,
    normalize_angle,
)


class TestAngularDistance:
    def test_same_point_is_zero(self):
        assert angular_distance(45.0, 90.0, 45.0, 90.0) == pytest.approx(0.0, abs=1e-10)

    def test_known_distance(self):
        dist = angular_distance(0.0, 0.0, 0.0, 90.0)
        assert dist == pytest.approx(90.0, abs=0.01)

    def test_pole_to_pole(self):
        dist = angular_distance(90.0, 0.0, -90.0, 0.0)
        assert dist == pytest.approx(180.0, abs=0.01)

    def test_symmetric(self):
        d1 = angular_distance(10.0, 20.0, 30.0, 40.0)
        d2 = angular_distance(30.0, 40.0, 10.0, 20.0)
        assert d1 == pytest.approx(d2, abs=1e-10)


class TestNormalizeAngle:
    def test_within_range(self):
        assert normalize_angle(45.0, 0.0, 360.0) == pytest.approx(45.0)

    def test_wrap_above(self):
        assert normalize_angle(370.0, 0.0, 360.0) == pytest.approx(10.0)

    def test_wrap_below(self):
        assert normalize_angle(-10.0, 0.0, 360.0) == pytest.approx(350.0)

    def test_exact_max_wraps(self):
        assert normalize_angle(360.0, 0.0, 360.0) == pytest.approx(0.0)


class TestClamp:
    def test_within(self):
        assert clamp(5.0, 0.0, 10.0) == 5.0

    def test_below(self):
        assert clamp(-1.0, 0.0, 10.0) == 0.0

    def test_above(self):
        assert clamp(15.0, 0.0, 10.0) == 10.0


class TestAltAzDelta:
    def test_simple_delta(self):
        d_alt, d_az = alt_az_delta(10.0, 20.0, 30.0, 40.0)
        assert d_alt == pytest.approx(20.0)
        assert d_az == pytest.approx(20.0)

    def test_shortest_path_positive_wrap(self):
        d_alt, d_az = alt_az_delta(0.0, 350.0, 0.0, 10.0)
        assert d_az == pytest.approx(20.0)

    def test_shortest_path_negative_wrap(self):
        d_alt, d_az = alt_az_delta(0.0, 10.0, 0.0, 350.0)
        assert d_az == pytest.approx(-20.0)


class TestConversions:
    def test_degrees_to_arcsec(self):
        assert degrees_to_arcsec(1.0) == pytest.approx(3600.0)

    def test_arcsec_to_degrees(self):
        assert arcsec_to_degrees(3600.0) == pytest.approx(1.0)

    def test_roundtrip(self):
        val = 0.5
        assert arcsec_to_degrees(degrees_to_arcsec(val)) == pytest.approx(val)
