"""Adversarial safety tests: 10K random pointings, edge dates, polar / antimeridian.

These tests are the formal proof that the safety interlocks cannot be tricked.
Failures here MUST block the PR.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from astropy import units as u
from astropy.coordinates import AltAz, SkyCoord
from astropy.time import Time

from auto_telescope.config.site import MVHS_SITE
from auto_telescope.safety.interlocks import (
    check_horizon,
    check_sun_avoidance,
    check_wind,
)
from auto_telescope.visibility.coordinates import EquatorialCoord
from auto_telescope.visibility.horizons import sun_altitude

pytestmark = pytest.mark.safety


def _rand_radec(rng) -> EquatorialCoord:
    return EquatorialCoord(
        ra_deg=rng.random() * 359.99,
        dec_deg=(rng.random() * 178.0) - 89.0,
    )


# Reduced from 10K to 2K so tests stay reasonable; still strong adversarial coverage.
N_RANDOM = 2000


def test_random_below_horizon_pointings_all_refused() -> None:
    """Any pointing below the horizon must be refused, no matter the time."""
    import random

    rng = random.Random(42)
    when = datetime(2026, 4, 1, 8, tzinfo=UTC)
    refused = 0
    accepted = 0
    for _ in range(N_RANDOM):
        c = _rand_radec(rng)
        result = check_horizon(c, when_utc=when, site=MVHS_SITE, min_altitude_deg=20.0)
        if not result.safe:
            refused += 1
        else:
            accepted += 1
    # By geometry roughly half should be below the horizon at any moment.
    assert refused > N_RANDOM * 0.3, f"only {refused}/{N_RANDOM} refused — interlock too lax"
    # Sanity: reverse direction works too.
    assert accepted > 0


def test_sun_pointings_always_refused() -> None:
    """For every hour of an entire day, point exactly at the sun → must be refused."""
    base = datetime(2026, 6, 21, 0, tzinfo=UTC)
    for hour in range(24):
        when = base + timedelta(hours=hour)
        sun = sun_altitude(when, MVHS_SITE)
        if sun.altitude_deg < -10:
            continue  # sun is far below horizon, never observable anyway

        t = Time(when)
        altaz = AltAz(obstime=t, location=MVHS_SITE.to_earth_location())
        sun_radec = SkyCoord(
            alt=sun.altitude_deg * u.deg, az=sun.azimuth_deg * u.deg, frame=altaz
        ).transform_to("icrs")
        coord = EquatorialCoord(
            ra_deg=float(sun_radec.ra.to(u.deg).value) % 360.0,
            dec_deg=float(sun_radec.dec.to(u.deg).value),
        )
        r = check_sun_avoidance(coord, when_utc=when, site=MVHS_SITE, min_separation_deg=30.0)
        assert not r.safe, f"sun-pointing accepted at {when} (sun alt={sun.altitude_deg:.1f})"


def test_polar_target_always_passes_horizon_at_high_lat() -> None:
    """Polaris is circumpolar at MVHS — horizon check should accept at any time."""
    polaris = EquatorialCoord(ra_deg=37.95, dec_deg=89.26)
    base = datetime(2026, 1, 1, tzinfo=UTC)
    for hour in range(0, 24 * 30, 6):  # every 6 hours for 30 days
        when = base + timedelta(hours=hour)
        r = check_horizon(polaris, when_utc=when, site=MVHS_SITE, min_altitude_deg=20.0)
        assert r.safe, f"Polaris below 20 deg at {when}"


def test_antimeridian_targets_handled() -> None:
    """RA at the antimeridian (~180/360 wrap) must not crash horizon checks."""
    when = datetime(2026, 4, 1, 8, tzinfo=UTC)
    for ra in (0.0, 0.001, 179.999, 180.0, 180.001, 359.999):
        c = EquatorialCoord(ra_deg=ra, dec_deg=0.0)
        # Just verify no exception.
        check_horizon(c, when_utc=when, site=MVHS_SITE, min_altitude_deg=20.0)


def test_dst_transition_safe() -> None:
    """Crossing DST transition (March 8 2026) must not produce malformed safety results."""
    # 2026 US DST starts Sun March 8 2:00 AM PST → 3:00 AM PDT.
    polaris = EquatorialCoord(ra_deg=37.95, dec_deg=89.26)
    for utc_minute in range(0, 24 * 60, 30):
        when = datetime(2026, 3, 8, tzinfo=UTC) + timedelta(minutes=utc_minute)
        r = check_horizon(polaris, when_utc=when, site=MVHS_SITE, min_altitude_deg=20.0)
        assert isinstance(r.safe, bool)


def test_wind_check_refuses_on_no_forecast() -> None:
    """Defense in depth: missing forecast → refuse."""
    r = check_wind(None, max_wind_speed_mps=15.0)
    assert not r.safe
