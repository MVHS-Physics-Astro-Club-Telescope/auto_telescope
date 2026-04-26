"""Tests for visibility.coordinates."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from auto_telescope.config.site import MVHS_SITE
from auto_telescope.visibility.coordinates import (
    AltAzPosition,
    EquatorialCoord,
    altaz_to_radec,
    angular_separation_deg,
    radec_to_altaz,
    slew_distance_deg,
)


class TestEquatorialCoord:
    def test_basic_construction(self) -> None:
        c = EquatorialCoord(ra_deg=180.0, dec_deg=0.0)
        assert c.ra_deg == 180.0
        assert c.dec_deg == 0.0

    def test_ra_wraps_around_360(self) -> None:
        c = EquatorialCoord(ra_deg=370.0, dec_deg=0.0)
        assert 0.0 <= c.ra_deg < 360.0

    @pytest.mark.parametrize("dec", [-90.5, 90.5, 100.0])
    def test_invalid_dec(self, dec: float) -> None:
        with pytest.raises(ValueError):
            EquatorialCoord(ra_deg=0.0, dec_deg=dec)


class TestRadecAltazRoundTrip:
    def test_round_trip_arcsec_precision(self) -> None:
        # M42 (Orion Nebula)
        m42 = EquatorialCoord(ra_deg=83.8221, dec_deg=-5.3911)
        when = datetime(2026, 1, 15, 4, 0, tzinfo=UTC)  # 8 PM PST
        altaz = radec_to_altaz(m42, when, MVHS_SITE)
        recovered = altaz_to_radec(altaz, MVHS_SITE)

        # Arcsecond-level round trip — within ~0.001 deg = 3.6 arcsec.
        assert abs((recovered.ra_deg - m42.ra_deg + 540.0) % 360.0 - 180.0) < 0.005
        assert abs(recovered.dec_deg - m42.dec_deg) < 0.005


class TestAngularSeparation:
    def test_zero_separation_for_identical_coords(self) -> None:
        c = EquatorialCoord(ra_deg=180.0, dec_deg=10.0)
        assert angular_separation_deg(c, c) == pytest.approx(0.0, abs=1e-6)

    def test_known_separation(self) -> None:
        # Same RA, dec offset by 10 deg → exactly 10 deg.
        a = EquatorialCoord(ra_deg=100.0, dec_deg=0.0)
        b = EquatorialCoord(ra_deg=100.0, dec_deg=10.0)
        assert angular_separation_deg(a, b) == pytest.approx(10.0, abs=1e-3)


class TestSlewDistance:
    def test_zero_for_same_position(self) -> None:
        p = AltAzPosition(
            altitude_deg=45.0, azimuth_deg=180.0, when_utc=datetime.now(UTC), site_name="x"
        )
        assert slew_distance_deg(p, p) == pytest.approx(0.0, abs=1e-6)

    def test_symmetric(self) -> None:
        when = datetime(2026, 1, 1, tzinfo=UTC)
        a = AltAzPosition(altitude_deg=30.0, azimuth_deg=90.0, when_utc=when, site_name="x")
        b = AltAzPosition(altitude_deg=60.0, azimuth_deg=270.0, when_utc=when, site_name="x")
        assert slew_distance_deg(a, b) == pytest.approx(slew_distance_deg(b, a), abs=1e-6)
