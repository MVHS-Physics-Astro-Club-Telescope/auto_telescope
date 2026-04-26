"""Unit tests for safety.interlocks (the most important module)."""

from __future__ import annotations

from datetime import UTC, datetime

from auto_telescope.conditions.aggregator import ConditionsForecast
from auto_telescope.config.site import MVHS_SITE
from auto_telescope.safety.interlocks import (
    check_can_slew,
    check_horizon,
    check_sun_avoidance,
    check_wind,
)
from auto_telescope.visibility.coordinates import EquatorialCoord


def _good_forecast() -> ConditionsForecast:
    return ConditionsForecast(
        hour_utc=datetime(2026, 7, 4, 6, tzinfo=UTC),
        cloud_cover_pct=10.0,
        wind_speed_mps=3.0,
        seeing_arcsec=1.5,
        transparency_mag=0.4,
        visibility_m=20000.0,
        temperature_c=20.0,
        relative_humidity_pct=40.0,
        contributing_providers=("7timer", "nws", "open-meteo"),
    )


class TestCheckHorizon:
    def test_above_horizon_passes(self) -> None:
        # Polaris from MVHS — always above horizon.
        polaris = EquatorialCoord(ra_deg=37.95, dec_deg=89.26)
        when = datetime(2026, 1, 15, 8, tzinfo=UTC)  # local midnight
        r = check_horizon(polaris, when_utc=when, site=MVHS_SITE, min_altitude_deg=20.0)
        assert r.safe

    def test_below_horizon_blocked(self) -> None:
        deep_south = EquatorialCoord(ra_deg=100.0, dec_deg=-70.0)
        when = datetime(2026, 4, 1, 8, tzinfo=UTC)
        r = check_horizon(deep_south, when_utc=when, site=MVHS_SITE, min_altitude_deg=20.0)
        assert not r.safe
        assert r.code == "below_horizon"


class TestCheckSunAvoidance:
    def test_sun_pointing_blocked(self) -> None:
        # Make a target near the sun's daytime position (sun is up at noon Pacific).
        # We can find the sun by querying its altitude and grabbing the AltAz.
        from astropy import units as u
        from astropy.coordinates import AltAz, SkyCoord
        from astropy.time import Time

        from auto_telescope.visibility.horizons import sun_altitude

        when = datetime(2026, 7, 4, 20, tzinfo=UTC)  # 1 PM PDT
        sun = sun_altitude(when, MVHS_SITE)
        t = Time(when)
        altaz = AltAz(obstime=t, location=MVHS_SITE.to_earth_location())
        sun_radec = SkyCoord(
            alt=sun.altitude_deg * u.deg, az=sun.azimuth_deg * u.deg, frame=altaz
        ).transform_to("icrs")
        sun_coord = EquatorialCoord(
            ra_deg=float(sun_radec.ra.to(u.deg).value) % 360.0,
            dec_deg=float(sun_radec.dec.to(u.deg).value),
        )
        r = check_sun_avoidance(sun_coord, when_utc=when, site=MVHS_SITE, min_separation_deg=30.0)
        assert not r.safe
        assert r.code == "sun_too_close"

    def test_far_target_passes(self) -> None:
        # Polaris at noon — opposite hemisphere of sun in summer.
        polaris = EquatorialCoord(ra_deg=37.95, dec_deg=89.26)
        when = datetime(2026, 7, 4, 20, tzinfo=UTC)
        r = check_sun_avoidance(polaris, when_utc=when, site=MVHS_SITE, min_separation_deg=30.0)
        assert r.safe


class TestCheckWind:
    def test_no_forecast_blocks(self) -> None:
        r = check_wind(None, max_wind_speed_mps=15.0)
        assert not r.safe
        assert r.code == "no_forecast"

    def test_wind_above_threshold_blocks(self) -> None:
        f = ConditionsForecast(
            hour_utc=datetime.now(UTC),
            cloud_cover_pct=10.0,
            wind_speed_mps=20.0,
            seeing_arcsec=1.0,
            transparency_mag=0.4,
            visibility_m=20000.0,
            temperature_c=20.0,
            relative_humidity_pct=40.0,
            contributing_providers=("nws",),
        )
        r = check_wind(f, max_wind_speed_mps=15.0)
        assert not r.safe
        assert r.code == "wind_too_high"

    def test_calm_passes(self) -> None:
        r = check_wind(_good_forecast(), max_wind_speed_mps=15.0)
        assert r.safe


class TestCheckCanSlew:
    def test_passes_when_all_clear(self) -> None:
        polaris = EquatorialCoord(ra_deg=37.95, dec_deg=89.26)
        when = datetime(2026, 1, 15, 8, tzinfo=UTC)
        r = check_can_slew(polaris, when_utc=when, site=MVHS_SITE, forecast=_good_forecast())
        assert r.safe, r.detail

    def test_returns_first_failure(self) -> None:
        # Below horizon should fail before wind check.
        deep_south = EquatorialCoord(ra_deg=100.0, dec_deg=-70.0)
        when = datetime(2026, 4, 1, 8, tzinfo=UTC)
        # Build a high-wind forecast — but horizon should fail first.
        bad_wind = ConditionsForecast(
            hour_utc=when,
            cloud_cover_pct=0.0,
            wind_speed_mps=50.0,
            seeing_arcsec=1.0,
            transparency_mag=0.4,
            visibility_m=20000.0,
            temperature_c=20.0,
            relative_humidity_pct=40.0,
            contributing_providers=("nws",),
        )
        r = check_can_slew(deep_south, when_utc=when, site=MVHS_SITE, forecast=bad_wind)
        assert not r.safe
        assert r.code == "below_horizon"
